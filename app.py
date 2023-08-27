from langchain import PromptTemplate, OpenAI, LLMChain
import streamlit as st

from langchain.chat_models import ChatOpenAI
from azureCognitiveSearch import getIcdCodes, getCptCodes
import openai
import os
import pandas as pd

from langchain.chains.openai_functions import (
    create_structured_output_chain
)
import streamlit as st
from firebaseFunctions import checkAuthentication, GetListOfTranscription, GetDetailsById
from tools import CPTCodeTool, ICD10CodeTool



tools = [
    ICD10CodeTool(), CPTCodeTool()
]

llm = ChatOpenAI(temperature=0, engine="GPT4", openai_api_key=st.secrets["AZURE_OPENAI_API_KEY"])


transcription='''Hello there Sir. How are you? Good. How are you? Good. There's not very much there as far as skills, but I can see a little bit of a rim to it, so I'm trying to get the little bit here. OK. And I feel this great feeling, but not painful. Yeah. How long has the spot been there? It started about two weeks. OK. He was travelling. [US_STATE] and then it's cleared up a lot in [US_STATE]. You wear this kind of athletic clothing most of the time. OK, alright, sure. Yeah, I don't think there's enough scale there too, so I don't, I don't think it's a fungal thing. And it just showed up out of nowhere. Yeah, nowhere, which is really freaked out, he said. It was a little bit more red, yeah, initially. And then with more scaly before. At this point it could be a little too. I didn't see like, so I was kind of looking. And were you wearing something like this in [US_STATE]? Ohh, yeah. It was really light, like a tank tops though. Yeah. Were you dealing with any foods like lime or lemon, celery or anything like that? Outside of what I ordered in room service, I got it pretty mellow. You got you weren't on someone's boat making. No, no, no, no. The pinnacle outline. Margaritas. OK, got it. And right now you said it's not symptomatic, it's not itchy for you at this point, not burning, not painful. It first started on my fingers, it work got super scaling dry and then when I noticed that I started examining my body and that's my countless probably just a little bit of post inflammatory hyperpigmentation and she said. Need to just use moisturizer. The one that they recommend for right now is called Seravee. Once you know that there's no irritation or itching at all, you could switch to something called amlactin. Amlactin is least expensive at Costco, as is the survey, and the amlactin will help to gently exfoliate. Don't get rid of the brown area, it doesn't look like there's anything remaining. May have had a rash that's gone and just left a little bit of brown. What happens is when we have a little bit of color in our skin, it's like the frosting. There are a cake has the color in it and it's vanilla cake underneath. If you put a birthday candle into the cake, you get pink frosting in the wrong area, right? And that's why it's a brown spot. So it's. Don't worry about it does not look like a cancer, like a bacterial viral fungal infection. Does not look like it's something seriously wrong inside of your body. OK, very much. See you back if you need us. Absolutely. Thank you.    
'''


from langchain.chains import LLMChain

from langchain.prompts import PromptTemplate
from prompt import notes_instruction, code_json_schema, code_instruction

prompt = PromptTemplate(input_variables=["transcription"], template= notes_instruction)
code_prompt = PromptTemplate(input_variables=["transcription"], template= code_instruction)



def display_codes_and_responses(code_output_json, medical_details):
    # Parse the JSON string to Python dictionary
    parsed_output = code_output_json

    # Display EM Code
    em_code = medical_details.get('EMCode', 'N/A')
    st.subheader(f"EM Code: {em_code}")
    st.json(code_output_json)
    # used_keys = set()

    # for icd_entry in parsed_output.get("medical_billing_codes", []):
    #     icd_code_display_name = icd_entry.get("ICD_10_code_display_name", "N/A")
    

    #     # Fetch ICD code options
    #     # icd_responses = getIcdCodes(icd_code_display_name)
        
    #     # Display the first ICD code option
    #     first_icd_option = f"{icd_code_display_name} "
        
    #     # Create a checkbox for the ICD code, auto-selected
    #     if first_icd_option not in used_keys:
    #         icd_selected = st.checkbox(first_icd_option, key=first_icd_option, value=True)
    #         used_keys.add(first_icd_option)
            


        # Start a bullet point list for the CPT codes
        

        # for cpt_entry in icd_entry.get("CPT_codes_display_name", []):
        #     cpt_code_display_name = cpt_entry.get("CPT_code_display_name", "N/A")
        #     if cpt_code_display_name == "N/A" or cpt_code_display_name == "Evaluation and Management":
        #         continue

        #     # Fetch CPT code options
        #     cpt_responses = getCptCodes(cpt_code_display_name)
            
        #     first_cpt_option = f"{cpt_code_display_name} : {cpt_responses[0]['Description']} ({cpt_responses[0]['id']})" if cpt_responses else 'N/A'
            
        #     # Create a checkbox for the CPT code, auto-selected
        #     if first_cpt_option not in used_keys:
        #         cpt_selected = st.checkbox(f" {first_cpt_option}", key=first_cpt_option, value=True)
        #         used_keys.add(first_cpt_option)
                   
            


# This function will handle the user authentication
def authenticate():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # Only show email and code input fields if the user is not authenticated
    if not st.session_state.authenticated:
        st.title("No Pajamas movement")
        email = st.text_input("Enter Email:")
        code = st.text_input("Enter Code:", type="password")

        if st.button("Authenticate"):
            st.session_state.authenticated = checkAuthentication(email, code)
            if st.session_state.authenticated:
                st.session_state.email = email
                st.success("Authenticated, please select date and patient from sidebar")
                st.experimental_rerun() 
            else:
                st.warning("Not Authenticated")
    else:
        st.success("Already authenticated, please select date and patient from sidebar")



# This function will handle the patient selection
# This function will handle the patient selection
def sidebar_patient_selection():
    st.sidebar.title("Filters")
    date = st.sidebar.date_input("Select Date Range:")
    patient_list = GetListOfTranscription(st.session_state.email, date)
    patient_names = [patient['patientName'] for patient in patient_list]
    
    # Initialize selected_patient_name in session_state if it's not already there
    if 'selected_patient_name' not in st.session_state:
        st.session_state.selected_patient_name = None

    st.sidebar.title("Patient Selection")
    new_selected_patient_name = st.sidebar.selectbox("Select a Patient:", patient_names)

    # Check if the patient has changed
    if st.session_state.selected_patient_name != new_selected_patient_name:
        st.session_state.selected_patient_name = new_selected_patient_name
        st.session_state.progress = 0  # Reset to the transcription view
        st.experimental_rerun()

    return next((patient['id'] for patient in patient_list if patient['patientName'] == new_selected_patient_name), None)


def display_medical_details(medical_details, billing_codes):
    display_codes_and_responses(billing_codes, medical_details)

    # Display other details
    st.title("Decision Report")

    st.subheader("Reasoning:")
    st.write(medical_details['Reasoning'])
    
    st.subheader("Criteria:")
    for criterion in medical_details['Criteria']:
        st.write(f"- {criterion}")

    st.subheader("Medical Decision Making (MDM) Level:")
    st.write(medical_details['MDMLevel'])
    
    st.subheader("Risk Level:")
    st.write(medical_details['RiskLevel'])
    
    st.subheader("Data Complexity:")
    st.write(medical_details['DataComplexity'])


def display_transcription(details):
    st.title('Transcription')
    col1, col2, col3 = st.columns([1,1, 1])
    with col3:
        if st.button('Next to Patient Note'):
            st.session_state.progress = 1
            st.experimental_rerun() 
    st.write(details['transcription'])
    

def display_patient_note(details):
    st.title('Patient Note')
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button('Back to Transcription'):
            st.session_state.progress = 0
            st.experimental_rerun() 
    with col3:
        if st.button('Next to Medical Codes'):
            st.session_state.progress = 2
            st.experimental_rerun() 
    st.write(details['patientNote'])
    

def display_medical_codes(details):
    st.title('Medical Codes')
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button('Back to Patient Note'):
            st.session_state.progress = 1
            st.experimental_rerun() 
    with col3:
        if st.button('Next to Patient Instructions'):
            st.session_state.progress = 3
            st.experimental_rerun() 
    display_medical_details(details['emcode'], details['patientMedicalCodes'])


def display_patient_instructions(details):
    st.title('Patient Instructions')
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button('Back to Medical Codes'):
            st.session_state.progress = 2
            st.experimental_rerun() 
    with col3:
        if st.button('Submit to EHR'):
            st.success('Error: EHR not connected')
    st.write(details['patientInstructions'])

def display_details(details):
    if st.session_state.progress == 0:
        display_transcription(details)
    elif st.session_state.progress == 1:
        display_patient_note(details)
    elif st.session_state.progress == 2:
        display_medical_codes(details)
    elif st.session_state.progress == 3:
        display_patient_instructions(details)

def transcription_page():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        authenticate()
        return

    selected_patient_id = sidebar_patient_selection()

    if selected_patient_id:
        details = GetDetailsById(selected_patient_id)
        display_details(details)

# Initialize session state
if 'progress' not in st.session_state:
    st.session_state.progress = 0

transcription_page()

