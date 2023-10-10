import firebase_admin
from firebase_admin import credentials, auth, firestore
import streamlit as st
from datetime import datetime, timezone
import random

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

def getCode(email):
    try:
        # Get the user by email
        user = auth.get_user_by_email(email)

        user_id = user.uid

        # Fetch code from Firestore
        user_doc_ref = db.collection('users').document(user_id)
        user_doc = user_doc_ref.get()
        stored_code = user_doc.to_dict().get('code', '')
        return stored_code
    except auth.UserNotFoundError:
        st.error('Email does not exist.')
        return False
    except Exception as e:
        st.error(f'An error occurred: {e}')
        return False

    

def getChildUsers(email):
    child_users_emails = [email]  # Initialize with the parent user's email

    try:
        # Get the user by email
        user = auth.get_user_by_email(email)
        user_id = user.uid

        # Fetch child users from Firestore subcollection
        child_users_ref = db.collection('users').document(user_id).collection('childUsers')
        child_users_docs = child_users_ref.stream()

        # Append child users' email to the list
        for doc in child_users_docs:
            child_users_emails.append(doc.to_dict().get('email', ''))

    except auth.UserNotFoundError:
        st.error('Email does not exist.')
    except Exception as e:
        st.error(f'An error occurred: {e}')

    return child_users_emails

def update_EHR_for_user(email, ehrType):
    user = auth.get_user_by_email(email)
    user_id = user.uid

    ehr_type_ref = db.collection('users').document(user_id)

    try:
        key = "ehrType"
        ehr_type_ref.update({
            key: ehrType
        })
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
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

def send_email_via_firestore(recipient_email, code):
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    MAIL_COLLECTION = 'mail'
    subject = f"Your MedScribe AI Login Code: {code}"

    message_text = f"""
    Hello,

    Thank you for using MedScribe AI!

    Your login code is: {code}

    Please enter this code into the application to proceed with the login.
    If you did not request this code, please ignore this email.

    Best,
    The MedScribe AI Team
    """

    message_html = f"""
    <p>Hello,</p>

    <p>Thank you for using <strong>MedScribe AI</strong>!</p>

    <p>Your login code is: <strong>{code}</strong></p>

    <p>Please enter this code into the application to proceed with the login. Please use this code everytime you login.</p>

    <p>If you did not request this code, please ignore this email.</p>

    <p>Best,<br/>
    The MedScribe AI Team</p>
    """

    # Construct the email message to be sent
    email_message = {
        'to': [recipient_email],
        'message': {
            'subject': subject,
            'text': message_text,
            'html': message_html,
        }
    }

    try:
        # Add the email message to Firestore, triggering the Firebase extension to send the email
        db.collection(MAIL_COLLECTION).add(email_message)
        print("Email queued for delivery!")
    except Exception as e:
        print(f"Failed to queue email: {e}")


def send_login_code_and_store(email):
    user = None
    code = None
    
    # Check if user exists
    try:
        user = auth.get_user_by_email(email)
        # Get existing code from Firestore
        user_doc = db.collection('users').document(user.uid).get()
        if user_doc.exists:
            code = user_doc.to_dict().get('code', None)
        else:
            # If user exists in auth but not in Firestore, create a document
            db.collection('users').document(user.uid).set({
                'email': email,
                # Add other initial user data here if needed
            })
    except auth.UserNotFoundError:
        # User not found, create new user in Firebase Auth
        user = auth.create_user(
            email=email,
            email_verified=True,
        )
        # Generate a new random code
        code = str(random.randint(1000, 9999))
        # Create user document in Firestore
        db.collection('users').document(user.uid).set({
            'email': email,
            'code': code,
            # Add other initial user data here if needed
        })

    # Send code via email
    send_email_via_firestore(email, code)

    # Only update the Firestore document with the code if it's newly generated
    if user and not code:
        try:
            db.collection('users').document(user.uid).update({
                'code': code
            })
        except Exception as e:
            st.error(f"Failed to store code in Firestore: {e}")

def store_uploaded_codes(email, file_content, file_codes_type):
    # Get user by email
    user = auth.get_user_by_email(email)
    user_id = user.uid
    
    # User document reference
    user_doc_ref = db.collection('users').document(user_id)
    
    try:
        # Update the user document with the uploaded content in 'cpt_codes'
        user_doc_ref.update({
            file_codes_type: file_content,
            'last_uploaded_at': firestore.SERVER_TIMESTAMP  # Server timestamp
        })
        st.success(file_codes_type + " uploaded successfully!")
    except Exception as e:
        st.error(f"An error occurred: {e}")

def retrieve_cpt_codes(email, file_codes_type):
    try:
        # Get user by email
        user = auth.get_user_by_email(email)
        user_id = user.uid
        
        # User document reference
        user_doc_ref = db.collection('users').document(user_id)
        user_doc = user_doc_ref.get()
        
        if user_doc.exists:
            # Retrieve 'cpt_codes' from user document
            cpt_codes = user_doc.to_dict().get(file_codes_type, '')
            return cpt_codes
        else:
            return None
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        return None

