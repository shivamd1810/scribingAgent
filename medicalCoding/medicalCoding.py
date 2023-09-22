


import openai
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
import os
import streamlit as st
import pandas as pd
import concurrent.futures
from firebaseFunctions import get_billing_code, update_billing_code
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

def read_text_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()
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
    cpt_em_list = []
    for item in data:
        if "EM_code_data" in item:
            icd_codes = "<br><br>".join([icd["ICD_10_code"] for icd in item["EM_code_data"]["associated_ICD_10_codes"]])
            icd_reasons = "<br><br>".join([icd["ICD_10_code_reason"] for icd in item["EM_code_data"]["associated_ICD_10_codes"]]) 
            cpt_em_list.append([item["EM_code_data"]["EM_code"], item["EM_code_data"]["EM_code_display_name"], icd_codes, item["EM_code_data"]["reason"], icd_reasons])
        elif "CPT_to_ICD_mapping" in item:
            for mapping in item["CPT_to_ICD_mapping"]:
                cpt_reason = mapping["reason"]
                for icd in mapping["associated_ICD_10_codes"]:
                    cpt_em_list.append([mapping["CPT_code"], mapping["CPT_code_display_name"], icd["ICD_10_code"], cpt_reason, icd["ICD_10_code_reason"]])
                    # Reset the CPT reason for subsequent ICD codes (to avoid repetition)
                    cpt_reason = ""

    cpt_em_df = pd.DataFrame(cpt_em_list, columns=["Code", "Description", "Associated ICD Code", "CPT Reason", "ICD Reason"])
    
    # Convert DataFrame to HTML and display using st.write()
    st.write(cpt_em_df.to_html(escape=False, index=False), unsafe_allow_html=True)


def display_info(transcription, patient_id):
  data = get_billing_code(patient_id)
  if data == '':
      patientType = st.radio("Select Patient Type:", ["First Visit", "Established Patient"])
      if st.button('Generate Notes'):
            # Assuming `transcription` is available or passed as an argument
            st.info("It takes around 90 seconds to generate billing codes.")
            # st.write("Generated notes:", new_patientMedicalCodes)  # Display the output
            data = generate_notes(transcription, patientType)
            display_tables(data)
            update_billing_code(patient_id, data) 
  else :
      display_tables(data)