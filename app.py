from langchain import PromptTemplate, OpenAI, LLMChain
import streamlit as st

from langchain.chat_models import ChatOpenAI
from azureCognitiveSearch import getIcdCodes, getCptCodes
import pandas as pd
from datetime import datetime, timedelta
from langchain.chains.openai_functions import (
    create_structured_output_chain
)
import streamlit as st
from firebaseFunctions import checkAuthentication, GetListOfTranscription, GetDetailsById, get_feedback, update_feedback, getChildUsers, send_login_code_and_store, update_EHR_for_user, getCode
from medicalCoding.medicalCoding import generate_notes, display_info
from medicalCoding.fhir.apiCall import FHIRApi
from tools import CPTCodeTool, ICD10CodeTool



tools = [
    ICD10CodeTool(), CPTCodeTool()
]
fhir_api = FHIRApi()

llm = ChatOpenAI(temperature=0, engine="GPT4", openai_api_key=st.secrets["AZURE_OPENAI_API_KEY"])


# transcription='''Hello there Sir. How are you? Good. How are you? Good. There's not very much there as far as skills, but I can see a little bit of a rim to it, so I'm trying to get the little bit here. OK. And I feel this great feeling, but not painful. Yeah. How long has the spot been there? It started about two weeks. OK. He was travelling. [US_STATE] and then it's cleared up a lot in [US_STATE]. You wear this kind of athletic clothing most of the time. OK, alright, sure. Yeah, I don't think there's enough scale there too, so I don't, I don't think it's a fungal thing. And it just showed up out of nowhere. Yeah, nowhere, which is really freaked out, he said. It was a little bit more red, yeah, initially. And then with more scaly before. At this point it could be a little too. I didn't see like, so I was kind of looking. And were you wearing something like this in [US_STATE]? Ohh, yeah. It was really light, like a tank tops though. Yeah. Were you dealing with any foods like lime or lemon, celery or anything like that? Outside of what I ordered in room service, I got it pretty mellow. You got you weren't on someone's boat making. No, no, no, no. The pinnacle outline. Margaritas. OK, got it. And right now you said it's not symptomatic, it's not itchy for you at this point, not burning, not painful. It first started on my fingers, it work got super scaling dry and then when I noticed that I started examining my body and that's my countless probably just a little bit of post inflammatory hyperpigmentation and she said. Need to just use moisturizer. The one that they recommend for right now is called Seravee. Once you know that there's no irritation or itching at all, you could switch to something called amlactin. Amlactin is least expensive at Costco, as is the survey, and the amlactin will help to gently exfoliate. Don't get rid of the brown area, it doesn't look like there's anything remaining. May have had a rash that's gone and just left a little bit of brown. What happens is when we have a little bit of color in our skin, it's like the frosting. There are a cake has the color in it and it's vanilla cake underneath. If you put a birthday candle into the cake, you get pink frosting in the wrong area, right? And that's why it's a brown spot. So it's. Don't worry about it does not look like a cancer, like a bacterial viral fungal infection. Does not look like it's something seriously wrong inside of your body. OK, very much. See you back if you need us. Absolutely. Thank you.    
# '''


from langchain.chains import LLMChain

from langchain.prompts import PromptTemplate
from prompt import notes_instruction, code_json_schema, code_instruction

prompt = PromptTemplate(input_variables=["transcription"], template= notes_instruction)
code_prompt = PromptTemplate(input_variables=["transcription"], template= code_instruction)

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

def display_feedback(patient_id, feedback_type):

    # Get existing feedback
    existing_feedback = get_feedback(patient_id, feedback_type)
    st.text("")
    st.text("")

    # Create text input field for feedback
    new_feedback = st.text_input(f"{feedback_type} Feedback : Let us know if you have any feedback for us/AI model", existing_feedback)

    # Create a button to update feedback
    if st.button(f"Submit Feedback"):
        if update_feedback(patient_id, new_feedback, feedback_type):
            st.success(f"{feedback_type} feedback updated successfully.")
            existing_feedback = new_feedback
        else:
            st.error(f"Failed to update {feedback_type} feedback.")

def authenticate():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # Only show email and code input fields if the user is not authenticated
    if not st.session_state.authenticated:
        st.title("Medscribe AI: No Pajamas movement")
        email = st.text_input("Enter Email:")
        code = st.text_input("Enter Code:", type="password")

        if st.button("Authenticate"):
            st.session_state.authenticated = checkAuthentication(email, code)
            if st.session_state.authenticated:
                st.session_state.email = email
                st.session_state.parentEmail = email
                st.success("Authenticated, please select date and patient from sidebar")
                st.experimental_rerun() 
            else:
                st.error("Email and code doesn't match, Not Authenticated")
        
        if st.button("First Time Here? Get Your Access Code"):
            if email:  # Check that the email is not empty
                send_login_code_and_store(email)  # Function to send the code via email
                st.success("A code has been sent to your email. Please use it to authenticate.")
            else:
                st.error("Please enter an email address.")
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


def display_email_selectbox_in_sidebar():
    # Fetch the email IDs using the previous function
    email = st.session_state.parentEmail
    email_ids = getChildUsers(email)
    
    # Display selectbox in the Streamlit sidebar
    selected_email = st.sidebar.selectbox("Choose an email ID:", email_ids)
    
    # Update session state with the selected email
    st.session_state.email = selected_email

def display_transcription(details):
    col1, col2, col3 = st.columns([1,1, 1])
    with col3:
        if st.button('Next to Patient Note'):
            st.session_state.progress = 1
            st.experimental_rerun()
    st.title('Transcription') 
    st.write(details['transcription'])
    

def display_patient_note(details, patient_id):
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button('Back to Transcription'):
            st.session_state.progress = 0
            st.experimental_rerun() 
    with col3:
        if st.button('Next to Patient Instructions'):
            st.session_state.progress = 2
            st.experimental_rerun() 
    st.title('Patient Note')
    st.write(details['patientNote'])
    display_feedback(patient_id, "PatientNotes")
    

def display_medical_codes(details, patient_id):
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button('Back to Patient Instructions'):
            st.session_state.progress = 2
            st.experimental_rerun() 
        
    with col3:
        if st.button('EHR submission'):
            st.session_state.progress = 4
            st.experimental_rerun() 
    
    st.title('Billing Codes')
    display_info(details["transcription"], patient_id)        
    display_feedback(patient_id, "BillingCodes")


def display_patient_instructions(details, patient_id):
    
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button('Back to Patient Notes'):
            st.session_state.progress = 1
            st.experimental_rerun() 

    with col3:
        if st.button('Next to Medical Codes'):
            st.session_state.progress = 3
            st.experimental_rerun()

    st.title('Patient Instructions')

    # Check if 'patientInstructions' and 'patient_instructions' are in details.
    if 'patientInstructions' in details and 'patient_instructions' in details['patientInstructions']:
        st.write(details['patientInstructions']['patient_instructions'])
        display_feedback(patient_id, "PatientInstructions")
    else:
        st.warning('Patient instructions are not available.')


def display_submit_ehr(details, patient_id) :
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button('Back to instructions'):
            st.session_state.progress = 3
            st.experimental_rerun() 
    # selected_patient_name = st.selectbox("Select Patient:", patient_names)
    st.write("")
    ehr_option = st.selectbox("Tell us which EHR do you use, our team will reach out to you for further details:", ["", "Cerner", "Epic", "Allscripts", "NextGen", "AthenaHealth", "Modmed", "Other"])

    # Providing an input box for users to type in their EHR name if "Other" is selected
    other_ehr_name = ""
    if ehr_option == "Other":
        other_ehr_name = st.text_input("Please specify the EHR name:")

    if st.button("Submit"):
    # Logic to handle the interaction with EHR can be added here
    # Depending on the EHR selection, you might have different integration/logic to add
    
    # Showing a message to all users upon submission
        if ehr_option == "Other" and other_ehr_name:
            st.success(f"Thank you for specifying your EHR: {other_ehr_name}. Our team will reach out to you for further help with integration.")
        else:
            st.success("Our team will reach out to you for further help with EHR integration.")
        update_EHR_for_user(st.session_state.parentEmail, ehr_option)

def display_details(details, patient_id):
    if st.session_state.progress == 0:
        display_transcription(details)
    elif st.session_state.progress == 1:
        display_patient_note(details, patient_id)
    elif st.session_state.progress == 2:
        display_patient_instructions(details, patient_id)
    elif st.session_state.progress == 3:
        display_medical_codes(details, patient_id)
    elif st.session_state.progress == 4:
        display_submit_ehr(details, patient_id)    

def transcription_page():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        authenticate()
        return

    display_email_selectbox_in_sidebar()
    selected_patient_id = sidebar_patient_selection()

    if selected_patient_id:
        details = GetDetailsById(selected_patient_id)
        display_details(details, selected_patient_id)
    else:
        user_email = st.session_state.email  # Replace with actual user email retrieval
        login_code = getCode(user_email)

        st.subheader("Let's Get Started with Your Transcription!")
        st.markdown(f"""
        It seems like there's no patient data available for transcription at the moment. 🕵️‍♂️

        To get started with live transcription during your sessions, download and utilize the **MedScribe AI** app as a listening device. Once the session concludes, the transcribed notes will magically appear here! 📝✨

        [📲 Download MedScribe AI](https://apps.apple.com/us/app/medscribe-ai/id6448894208)

        ** Use the following code to log in: {login_code} **

        Simply use the app during your patient sessions, and once you end the session in the app, you'll be able to view and manage your patient notes here. Let’s streamline your documentation process together! 🚀🤝
        """)


# Initialize session state
if 'progress' not in st.session_state:
    st.session_state.progress = 0

transcription_page()

