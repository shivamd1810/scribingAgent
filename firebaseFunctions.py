import firebase_admin
from firebase_admin import credentials, auth, firestore
import streamlit as st
from datetime import datetime, timezone

cred_dict = {
    "type": st.secrets["type"],
    "project_id": st.secrets["project_id"],
    "private_key_id": st.secrets["private_key_id"],
    "private_key": st.secrets["private_key"],
    "client_email": st.secrets["client_email"],
    "client_id": st.secrets["client_id"],
    "auth_uri": st.secrets["auth_uri"],
    "token_uri": st.secrets["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["client_x509_cert_url"]
}

# Initialize Firestore
try:
    # Attempt to get the default app
    firebase_admin.get_app()
except ValueError:
    # If it fails, initialize the app here
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
db = firestore.client()

def checkAuthentication(email, code):
    try:
        # Get the user by email
        user = auth.get_user_by_email(email)

        user_id = user.uid

        # Fetch code from Firestore
        user_doc_ref = db.collection('users').document(user_id)
        user_doc = user_doc_ref.get()
        stored_code = user_doc.to_dict().get('code', '')

        # Check if the code matches
        if code == str(stored_code):
            return True
        else:
            return False
    except auth.UserNotFoundError:
        st.error('Email does not exist.')
        return False
    except Exception as e:
        st.error(f'An error occurred: {e}')
        return False

def GetListOfTranscription(email, date):
    # Get the user by email
    user = auth.get_user_by_email(email)
    user_id = user.uid
    
    # Convert date to an 'aware' datetime object with UTC timezone
    # The starting time of the date
    start_datetime = datetime.combine(date, datetime.min.time(), timezone.utc)
    
    # The ending time of the date (one second before the next day starts)
    end_datetime = datetime.combine(date, datetime.max.time(), timezone.utc)

    # Fetch patientNames for the given date range
    patient_names_ref = db.collection('users').document(user_id).collection('patientNames')
    
    # Use the 'aware' datetime objects in the query
    query = patient_names_ref.where('visitDate', '>=', start_datetime).where('visitDate', '<=', end_datetime)
    
    patient_docs = query.stream()

    patient_list = []
    for patient_doc in patient_docs:
        patient_data = patient_doc.to_dict()
        patient_list.append({
            'patientName': patient_data.get('patientName', ''),
            'id': patient_doc.id
        })

    return patient_list

def GetDetailsById(patient_id):
    patient_visit_ref = db.collection('patientVisits').document(patient_id)
    patient_visit_doc = patient_visit_ref.get()

    result = {
        'transcription': 'No transcription available.',
        'emcode': 'No EM code available.',
        'patientMedicalCodes': 'No medical codes available.',
        'patientInstructions': 'No instructions available.',
        'patientNote': 'No notes available.'
    }

    if patient_visit_doc.exists:
        patient_data = patient_visit_doc.to_dict()
        
        result['transcription'] = patient_data.get('transcription', 'No transcription available.')
        result['emcode'] = patient_data.get('emcode', 'No EM code available.')
        result['patientMedicalCodes'] = patient_data.get('patientMedicalCodes', 'No medical codes available.')
        result['patientInstructions'] = patient_data.get('patientInstructions', 'No instructions available.')
        result['patientNote'] = patient_data.get('patientNote', 'No notes available.')

    else:
        result['transcription'] = 'No record found for this patient ID.'

    return result

def get_feedback(patient_id, feedback_type):
    # Document reference for the specific patient visit
    patient_visit_ref = db.collection('patientVisits').document(patient_id)

    # Fetch the existing document
    patient_visit_doc = patient_visit_ref.get()

    if patient_visit_doc.exists:
        patient_data = patient_visit_doc.to_dict()
        key = f"{feedback_type}Feedback"  # E.g., 'MedicalCodesFeedback'
        return patient_data.get(key, '')
    else:
        return ''

def update_feedback(patient_id, new_feedback, feedback_type):
    # Document reference for the specific patient visit
    patient_visit_ref = db.collection('patientVisits').document(patient_id)

    try:
        key = f"{feedback_type}Feedback"  # E.g., 'MedicalCodesFeedback'
        # Update the document with new feedback
        patient_visit_ref.update({
            key: new_feedback
        })
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def update_billing_code(patient_id, billing_code):
    # Document reference for the specific patient visit
    patient_visit_ref = db.collection('patientVisits').document(patient_id)

    try:
        key = "billingCodes"  # E.g., 'MedicalCodesFeedback'
        # Update the document with new feedback
        patient_visit_ref.update({
            key: billing_code
        })
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def get_billing_code(patient_id):
    # Document reference for the specific patient visit
    patient_visit_ref = db.collection('patientVisits').document(patient_id)

    # Fetch the existing document
    patient_visit_doc = patient_visit_ref.get()

    if patient_visit_doc.exists:
        patient_data = patient_visit_doc.to_dict()
        key = "billingCodes"  # E.g., 'MedicalCodesFeedback'
        return patient_data.get(key, '')
    else:
        return ''