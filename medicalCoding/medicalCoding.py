


import openai
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
import os
import streamlit as st
import pandas as pd
from collections import defaultdict
import concurrent.futures


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
  #  icd_code_list =  {'ICD_10_codes': [{'ICD_10_code': 'L21.0', 'ICD_10_code_display_name': 'Seborrhea capitis'}, {'ICD_10_code': 'L21.8', 'ICD_10_code_display_name': 'Other seborrheic dermatitis'}, {'ICD_10_code': 'L60.0', 'ICD_10_code_display_name': 'Ingrowing nail'}, {'ICD_10_code': 'L65.8', 'ICD_10_code_display_name': 'Other specified nonscarring hair loss'}, {'ICD_10_code': 'L70.0', 'ICD_10_code_display_name': 'Acne vulgaris'}, {'ICD_10_code': 'L82.1', 'ICD_10_code_display_name': 'Other seborrheic keratosis'}, {'ICD_10_code': 'L85.3', 'ICD_10_code_display_name': 'Xerosis cutis'}, {'ICD_10_code': 'B35.3', 'ICD_10_code_display_name': 'Tinea pedis'}]}
   with concurrent.futures.ThreadPoolExecutor() as executor:
        future_cpt = executor.submit(get_cpt_code_list, transcription, icd_code_list, cptcodes)
        future_em = executor.submit(get_em_code_list, transcription, icd_code_list, eminstruction, patientType)
        
        # Retrieve the results once they are done
        cpt_code_list = future_cpt.result()
        em_code_list = future_em.result()   

   return [em_code_list, cpt_code_list]


import streamlit as st
import pandas as pd


# # Sample data
data = [
  {
    "CPT_to_ICD_mapping": [
      {
        "CPT_code": "17110",
        "CPT_code_display_name": "Destruct B9 Lesion 1-14",
        "reason": "The patient has seborrheic keratosis which can be treated by destruction of benign lesions.",
        "associated_ICD_10_codes": [
          {
            "ICD_10_code": "L82.1",
            "ICD_10_code_display_name": "Other seborrheic keratosis"
          }
        ]
      },
      {
        "CPT_code": "11900",
        "CPT_code_display_name": "Inject Skin Lesions </W 7",
        "reason": "The patient has seborrheic dermatitis and acne vulgaris which can be treated by injection of skin lesions.",
        "associated_ICD_10_codes": [
          {
            "ICD_10_code": "L21.8",
            "ICD_10_code_display_name": "Other seborrheic dermatitis"
          },
          {
            "ICD_10_code": "L70.0",
            "ICD_10_code_display_name": "Acne vulgaris"
          }
        ]
      },
      {
        "CPT_code": "17260",
        "CPT_code_display_name": "Destruction Of Skin Lesions",
        "reason": "The patient has seborrheic keratosis which can be treated by destruction of skin lesions.",
        "associated_ICD_10_codes": [
          {
            "ICD_10_code": "L82.1",
            "ICD_10_code_display_name": "Other seborrheic keratosis"
          }
        ]
      }
    ]
  },
  {
    "EM_code_data": {
      "EM_code": "99204",
      "EM_code_display_name": "New patient office or other outpatient visit, typically 45 minutes",
      "reason": "The patient is a new patient with multiple issues including seborrheic dermatitis, seborrheic keratosis, nonscarring hair loss, and tinea pedis. The physician reviewed the patient's history, conducted a thorough examination, and provided a detailed treatment plan.",
      "associated_ICD_10_codes": [
        {
          "ICD_10_code": "L21.8",
          "ICD_10_code_display_name": "Other seborrheic dermatitis",
          "ICD_10_code_reason": "The patient has dandruff on the forehead and hair, which is a form of seborrheic dermatitis."
        },
        {
          "ICD_10_code": "L82.1",
          "ICD_10_code_display_name": "Other seborrheic keratosis",
          "ICD_10_code_reason": "The patient has seborrheic keratosis on the back and other parts of the body."
        },
        {
          "ICD_10_code": "L65.8",
          "ICD_10_code_display_name": "Other specified nonscarring hair loss",
          "ICD_10_code_reason": "The patient is experiencing hair loss, which is a form of nonscarring hair loss."
        },
        {
          "ICD_10_code": "B35.3",
          "ICD_10_code_display_name": "Tinea pedis",
          "ICD_10_code_reason": "The patient has a fungal infection between the toes, also known as tinea pedis or athlete's foot."
        }
      ]
    }
  }
]

def display_tables(transcription, patientType) :
    data = generate_notes(transcription, patientType)
    icd_list = []
    for item in data:
        if "EM_code_data" in item:
            for icd_code in item["EM_code_data"]["associated_ICD_10_codes"]:
                icd_list.append([icd_code["ICD_10_code"], icd_code["ICD_10_code_display_name"]])
        elif "CPT_to_ICD_mapping" in item:
            for mapping in item["CPT_to_ICD_mapping"]:
                for icd_code in mapping["associated_ICD_10_codes"]:
                    icd_list.append([icd_code["ICD_10_code"], icd_code["ICD_10_code_display_name"]])
    icd_df = pd.DataFrame(icd_list, columns=["ICD_10_code", "ICD_10_code_display_name"]).drop_duplicates()
    st.write("## icd codes")
    st.table(icd_df)

    # Table 2: Each CPT or EM code has a correspondent list of ICD codes
    cpt_em_list = []
    for item in data:
        if "EM_code_data" in item:
            icd_codes = ", ".join([icd["ICD_10_code"] for icd in item["EM_code_data"]["associated_ICD_10_codes"]])
            cpt_em_list.append([item["EM_code_data"]["EM_code"], item["EM_code_data"]["EM_code_display_name"], icd_codes, item["EM_code_data"]["reason"]])
        elif "CPT_to_ICD_mapping" in item:
            for mapping in item["CPT_to_ICD_mapping"]:
                icd_codes = ", ".join([icd["ICD_10_code"] for icd in mapping["associated_ICD_10_codes"]])
                cpt_em_list.append([mapping["CPT_code"], mapping["CPT_code_display_name"], icd_codes, mapping["reason"]])

        
    cpt_em_df = pd.DataFrame(cpt_em_list, columns=["Code", "Description", "Associated ICD Codes", "Reason"])
    st.write("## CPT code")
    st.table(cpt_em_df)

def display_info(transcription, patientType):
  display_tables(transcription, patientType)