import openai
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
import os
import streamlit as st
import pandas as pd
import concurrent.futures
from firebaseFunctions import get_billing_code, update_billing_code, store_uploaded_codes
from langchain.prompts import PromptTemplate
from .prompt import cpt_instruction, cpt_json_schema, icd_instruction, icd_json_schema, em_code, em_instruction
from langchain.chains.openai_functions import (
    create_structured_output_chain
)


openai.api_type = "azure"
openai.api_key = os.getenv('AZURE_OPENAI_API_KEY')
openai.api_base = "https://medscribeai.openai.azure.com"
openai.api_version = "2023-07-01-preview"

llm32 = ChatOpenAI(temperature=0, engine="gpt432k", openai_api_key=openai.api_key)
llm8 = ChatOpenAI(temperature=0, engine="GPT4", openai_api_key=openai.api_key)
icd_prompt = PromptTemplate(input_variables=["transcription", "icdCodes"], template= icd_instruction)
cpt_prompt = PromptTemplate(input_variables=["transcription", "icdCodes", "cptCodes"], template= cpt_instruction)
em_prompt = PromptTemplate(input_variables=["transcription", "icdCodes", "emGuidelines", "patientType"], template= em_instruction)

def read_text_file(filepath):
    with open(filepath, 'r') as f:
        lines = [line.strip().split('\t') for line in f.readlines()]
    return lines
    
import os
print(os.getcwd())
eminstruction = read_text_file('./medicalCoding/eminstructions.txt')
icdcodes = read_text_file('./medicalCoding/icd10Codes.txt')
cptcodes = read_text_file('./medicalCoding/cptCodes.txt')

icd_llmchain = create_structured_output_chain(icd_json_schema, llm32, icd_prompt, verbose=True)
cpt_llmchain = create_structured_output_chain(cpt_json_schema, llm8, cpt_prompt, verbose=True)
em_llmchain = create_structured_output_chain(em_code, llm8, em_prompt, verbose=True)

def get_cpt_code_list(transcription, icd_code_list, cptcodes):
    return cpt_llmchain.run({
        "transcription": transcription,
        "icdCodes": icd_code_list,
        "cptCodes": cptcodes
    })

def get_em_code_list(transcription, icd_code_list, eminstruction, patientType):
    return em_llmchain.run({
        "transcription": transcription,
        "icdCodes": icd_code_list,
        "emGuidelines": eminstruction,
        "patientType": patientType
    })

@st.cache_data
def generate_notes(transcription, patientType):
   icd_code_list = icd_llmchain.run({"transcription":transcription,  "icdCodes":icdcodes})
  #  icd_code_list =  {'ICD_10_codes': [{'ICD_10_code': 'L21.0', 'ICD_10_code_display_name': 'Seborrhea capitis', 'reason': 'The patient was observed to have some flaking in the hair and on the forehead, which the doctor identified as dandruff. The doctor recommended using dandruff shampoo to manage the condition.'}, {'ICD_10_code': 'L60.3', 'ICD_10_code_display_name': 'Nail dystrophy', 'reason': 'The patient mentioned using a product to promote hair growth, which could potentially affect the nails as well. The doctor did not specify any nail abnormalities, but this code could be considered if further information confirms nail changes.'}, {'ICD_10_code': 'L65.9', 'ICD_10_code_display_name': 'Nonscarring hair loss, unspecified', 'reason': 'The patient was observed to be losing some hair. The doctor discussed a treatment option involving a foam that promotes hair growth.'}, {'ICD_10_code': 'L82.1', 'ICD_10_code_display_name': 'Other seborrheic keratosis', 'reason': 'The patient was observed to have some seborrheic keratosis. The doctor identified these as normal and did not recommend any treatment unless they become bothersome to the patient.'}, {'ICD_10_code': 'B35.3', 'ICD_10_code_display_name': 'Tinea pedis', 'reason': "The patient was observed to have a fungal infection between the toes, commonly known as athlete's foot. The doctor recommended using clotrimazole to treat the condition."}, {'ICD_10_code': 'L81.8', 'ICD_10_code_display_name': 'Other specified disorders of pigmentation', 'reason': 'The patient mentioned noticing more visible blood vessels on his skin. The doctor identified this as a normal part of aging and did not recommend any treatment unless it becomes a cosmetic concern.'}, {'ICD_10_code': 'D22.9', 'ICD_10_code_display_name': 'Melanocytic nevi, unspecified', 'reason': 'The patient was observed to have some moles, which the doctor identified as normal. The doctor used an instrument to examine the moles and confirmed that they were normal.'}]}
   with concurrent.futures.ThreadPoolExecutor() as executor:
        future_cpt = executor.submit(get_cpt_code_list, transcription, icd_code_list, cptcodes)
        future_em = executor.submit(get_em_code_list, transcription, icd_code_list, eminstruction, patientType)
        
        # Retrieve the results once they are done
        cpt_code_list = future_cpt.result()
        em_code_list = future_em.result()   

   return [em_code_list, cpt_code_list]


import streamlit as st
import pandas as pd


# # # Sample data
# data = [
#   {
#     "CPT_to_ICD_mapping": [
#       {
#         "CPT_code": "17110",
#         "CPT_code_display_name": "Destruct B9 Lesion 1-14",
#         "reason": "The patient has seborrheic keratosis which can be treated by destruction of benign lesions.",
#         "associated_ICD_10_codes": [
#           {
#             "ICD_10_code": "L82.1",
#             "ICD_10_code_display_name": "Other seborrheic keratosis"
#           }
#         ]
#       },
#       {
#         "CPT_code": "11900",
#         "CPT_code_display_name": "Inject Skin Lesions </W 7",
#         "reason": "The patient has seborrheic dermatitis and acne vulgaris which can be treated by injection of skin lesions.",
#         "associated_ICD_10_codes": [
#           {
#             "ICD_10_code": "L21.8",
#             "ICD_10_code_display_name": "Other seborrheic dermatitis"
#           },
#           {
#             "ICD_10_code": "L70.0",
#             "ICD_10_code_display_name": "Acne vulgaris"
#           }
#         ]
#       },
#       {
#         "CPT_code": "17260",
#         "CPT_code_display_name": "Destruction Of Skin Lesions",
#         "reason": "The patient has seborrheic keratosis which can be treated by destruction of skin lesions.",
#         "associated_ICD_10_codes": [
#           {
#             "ICD_10_code": "L82.1",
#             "ICD_10_code_display_name": "Other seborrheic keratosis"
#           }
#         ]
#       }
#     ]
#   },
#   {
#     "EM_code_data": {
#       "EM_code": "99204",
#       "EM_code_display_name": "New patient office or other outpatient visit, typically 45 minutes",
#       "reason": "The patient is a new patient with multiple issues including seborrheic dermatitis, seborrheic keratosis, nonscarring hair loss, and tinea pedis. The physician reviewed the patient's history, conducted a thorough examination, and provided a detailed treatment plan.",
#       "associated_ICD_10_codes": [
#         {
#           "ICD_10_code": "L21.8",
#           "ICD_10_code_display_name": "Other seborrheic dermatitis",
#           "ICD_10_code_reason": "The patient has dandruff on the forehead and hair, which is a form of seborrheic dermatitis."
#         },
#         {
#           "ICD_10_code": "L82.1",
#           "ICD_10_code_display_name": "Other seborrheic keratosis",
#           "ICD_10_code_reason": "The patient has seborrheic keratosis on the back and other parts of the body."
#         },
#         {
#           "ICD_10_code": "L65.8",
#           "ICD_10_code_display_name": "Other specified nonscarring hair loss",
#           "ICD_10_code_reason": "The patient is experiencing hair loss, which is a form of nonscarring hair loss."
#         },
#         {
#           "ICD_10_code": "B35.3",
#           "ICD_10_code_display_name": "Tinea pedis",
#           "ICD_10_code_reason": "The patient has a fungal infection between the toes, also known as tinea pedis or athlete's foot."
#         }
#       ]
#     }
#   }
# ]
def display_tables(data):
    icd_combined_list = [f"{code[0]} - {code[1]}" for code in icdcodes[1:]]
    cpt_combined_list = [""] + [f"{code[0]} - {code[1]}" for code in cptcodes[1:]]

    
    new_cpt_code = st.selectbox("Select CPT code", cpt_combined_list, index=0)

    # Multi select option for ICD code
    selected_multiple_icd_codes = st.multiselect("Select Multiple ICD 10 Codes", icd_combined_list)

    # Button to add to table
    if st.button("Add"):
        cpt_code, cpt_display_name = new_cpt_code.split(' - ', 1)
        # Splitting the combined list for ICD codes and descriptions
        selected_icd_codes = [code_combined.split(' - ', 1)[0] for code_combined in selected_multiple_icd_codes]
        selected_icd_display_names = [code_combined.split(' - ', 1)[1] for code_combined in selected_multiple_icd_codes]

        new_mapping = {
            "CPT_to_ICD_mapping": [{
                "CPT_code": cpt_code,
                "CPT_code_display_name": cpt_display_name,
                "reason": "Manually added",
                "associated_ICD_10_codes": [
                    {
                        "ICD_10_code": icd_code,
                        "ICD_10_code_reason": "Manually added:" + icd_display_name
                    } for icd_code, icd_display_name in zip(selected_icd_codes, selected_icd_display_names)
                ]
            }]
        }
        data.append(new_mapping)

    cpt_em_list = []
    
    for item in data:
        if "EM_code_data" in item:
            icd_codes = [icd["ICD_10_code"] for icd in item["EM_code_data"]["associated_ICD_10_codes"]]
            icd_reasons =  "   |    ".join([icd["ICD_10_code_reason"] for icd in item["EM_code_data"]["associated_ICD_10_codes"]])

            
            cpt_em_list.append([True, item["EM_code_data"]["EM_code"], icd_codes, item["EM_code_data"]["EM_code_display_name"], item["EM_code_data"]["reason"], icd_reasons])
        
        elif "CPT_to_ICD_mapping" in item:
            for mapping in item["CPT_to_ICD_mapping"]:
                cpt_reason = mapping["reason"]
                
                icd_codes = []
                icd_reasons = ""
                
                for icd in mapping["associated_ICD_10_codes"]:
                    icd_codes.append(icd["ICD_10_code"])
                    icd_reasons = icd_reasons + "   |    " + icd["ICD_10_code_reason"] if icd_reasons else icd["ICD_10_code_reason"]
                
                cpt_em_list.append([True, mapping["CPT_code"], icd_codes, mapping["CPT_code_display_name"], cpt_reason, icd_reasons])
                
                # Reset the CPT reason for subsequent ICD codes (to avoid repetition)
                cpt_reason = ""
    cpt_em_df = pd.DataFrame(cpt_em_list, columns=["Selected", "Code", "Associated ICD Code", "Description", "CPT Reason", "ICD Reason"])

    
    # Convert DataFrame to HTML and display using st.write()
    edited_cpt_em_df = st.data_editor(cpt_em_df, hide_index=True)

    # Filter the rows where "Selected" is False
    deselected_rows = edited_cpt_em_df[~edited_cpt_em_df["Selected"]]

    # Now remove these deselected rows from your original data
    for index, row in deselected_rows.iterrows():
        code = row["Code"]
        data = [item for item in data if not (item.get("EM_code_data", {}).get("EM_code") == code or any(mapping.get("CPT_code") == code for mapping in item.get("CPT_to_ICD_mapping", [])))]

    return data

def display_info( transcription, patient_id):
    data = get_billing_code(patient_id)
    
    if "@dermatologyarts.com" not in st.session_state.email:
        st.markdown('''
            <div style="border:2px solid #f63366; padding:20px; border-radius:10px;">
                <p>
                It appears you are a new customer. To ensure seamless integration 
                with our model, we need your practice's CPT and ICD10 codes from the last year. 
                <strong>Please send these files directly to 
                <a href="mailto:shivam@themedscribe.ai">shivam@themedscribe.ai</a></strong>.
                </p>
                <p>
                Once we receive your data, it will take approximately <strong>1 day</strong> 
                to configure our model. Should you have any questions or require 
                expedited service, feel free to reach out through the same email.
                </p>
                <p>Thank you for choosing us!</p>
            </div>
        ''', unsafe_allow_html=True)
    elif data == '':
        patientType = st.radio("Select Patient Type:", ["First Visit", "Established Patient"])
        if st.button('Generate Notes'):
            st.info("It takes around 90 seconds to generate billing codes.")
            data = generate_notes(transcription, patientType)
            data = display_tables(data)
            update_billing_code(patient_id, data) 
    else:
        data = display_tables(data)
        update_billing_code(patient_id, data)