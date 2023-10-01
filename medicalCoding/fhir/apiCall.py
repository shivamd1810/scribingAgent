import os
import requests
import json
import logging
import datetime
from io import BytesIO
from PyPDF2 import PdfFileReader
from datetime import datetime, time
# from weasyprint import HTML


class FHIRApi:
    def __init__(self):
        self.base_url = 'https://stage.ema-api.com/ema-training/firm/dermarts/ema/fhir/v2'
        self.auth_url = 'https://stage.ema-api.com/ema-training/firm/dermarts/ema/ws/oauth2/grant'
        self.api_key = '9a32ae6b-cc6c-4775-a619-e05fd3705457'
        self.refresh_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJmaGlyX0pxZ1hiIiwidXJsUHJlZml4IjoiZGVybWFydHMiLCJpc3MiOiJtb2RtZWQiLCJ0b2tlblR5cGUiOiJyZWZyZXNoIiwianRpIjoiNGI2OTZhNWY0MTYyNDcxMjlmMjQ0OTkxYjk4ZDQzYzcifQ.X7KgBQd-ADLrwnSqf-5SuqZ4LgMacP5k5IEJ7mkYLCU"
        self.bearer_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJmaGlyX0pxZ1hiIiwicG9sICAgICAgICAiOiJjaGFuZ2VtZSIsInVybFByZWZpeCI6ImRlcm1hcnRzIiwidmVuZG9yIjoiZmhpcl9KcWdYYkBkZXJtYXJ0cyIsImlzcyI6Im1vZG1lZCIsInRva2VuVHlwZSI6ImFjY2VzcyIsImp0aSI6ImQ3Y2IyYjgwOTU5ODRjYTFiNGE0MjE0NmM4YThmZWUyIn0.xmmShOomRf7qb1f3d6yE56cw_lR8D3HREy4nST8sv-0"
        if self.api_key is None:
            raise Exception('FHIR_API_KEY environment variable not found')

    def _get_headers(self, with_auth=True):
        headers = {
            'Content-Type': 'application/fhir+json',
            'x-api-key': self.api_key
        }
        if with_auth:
            headers['Authorization'] = f'Bearer {self.bearer_token}'
        return headers

    def _handle_response(self, response, endpoint):
        if response.status_code == 401:  # Assuming 401 indicates an expired token
            # Refresh the token
            self.bearer_token = self._refresh_access_token()
            headers = self._get_headers()
            # Retry the request with the new token
            response = requests.get(f'{self.base_url}/{endpoint}', headers=headers)
        if response.status_code != 200:
            logging.error("Failed to retrieve data from %s. Status Code: %s, Response: %s", endpoint, response.status_code, response.text)
            return None
        return response.json()

    def _refresh_access_token(self):
        headers = self._get_headers(with_auth=False)
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        response = requests.post(self.auth_url, headers=headers, data=data)
        return response.json().get('access_token')

    def get_patient_ids(self, practitioner_id, start_date=None, end_date=None, status="arrived"):
        """
        :param practitioner_id: ID of the practitioner
        :param start_date: The starting date in 'YYYY-MM-DD' format. Defaults to None.
        :param end_date: The ending date in 'YYYY-MM-DD' format. Defaults to None.
        :param status: The status filter. Defaults to 'arrived'.
        :return: List of patient IDs.
        """

        # Convert the provided dates to the required format, if they are given.
        if start_date:
            start_datetime = datetime.combine(datetime.strptime(start_date, '%Y-%m-%d').date(), time.min)
            start_date = start_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        if end_date:
            end_datetime = datetime.combine(datetime.strptime(end_date, '%Y-%m-%d').date(), time.max)
            end_date = end_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
        
        # Build the endpoint URL with the provided filters.
        endpoint = f"Appointment?status={status}&practitioner={practitioner_id}"
        if start_date:
            endpoint += f"&date=ge{start_date}"
        if end_date:
            endpoint += f"&date=le{end_date}"

        response = requests.get(f'{self.base_url}/{endpoint}', headers=self._get_headers())
        data = self._handle_response(response, endpoint)
        
        print(data)
        patient_ids = []
        if data:
            for entry in data.get("entry", []):
                for participant in entry.get("resource", {}).get("participant", []):
                    reference = participant.get("actor", {}).get("reference", "")
                    if "Patient/" in reference:
                        patient_ids.append(reference.split("Patient/")[1])
        return patient_ids

    def get_patient_name_by_id(self, patient_id):
        endpoint = f"Patient/{patient_id}"
        response = requests.get(f'{self.base_url}/{endpoint}', headers=self._get_headers())
        data = self._handle_response(response, endpoint)
        
        if not data:
            return None
        
        name_data = data.get("name", [{}])[0]
        return " ".join(name_data.get("given", []) + [name_data.get("family", "")])

    def call_api(self, endpoint, data):
        headers = self._get_headers()
        response = requests.post(f'{self.base_url}/{endpoint}', headers=headers, data=json.dumps(data))
        
        print(response.status_code)
        print(response.text)
        
        data = self._handle_response(response, endpoint)
    
    def post_to_fhir(self, transcription, patientId, encounterId, practitionerId, visit_note):
        patient = {
            "reference": f"Patient/{patientId}",
            "display": f"Patient/{patientId}"
        }

        practitioner = {
            "reference": f"Practitioner/{practitionerId}",
            "display": f"Practitioner/{practitionerId}"
        }

        encounter = {
            "reference": f"Encounter/{encounterId}",
            "display": f"Encounter/{encounterId}"
        }
    
        self.composition(patient, encounter, practitioner, visit_note)

    def get_s3_url(self):
        headers = {
            'x-api-key': '9a32ae6b-cc6c-4775-a619-e05fd3705457',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJmaGlyX0pxZ1hiIiwicG9sICAgICAgICAiOiJjaGFuZ2VtZSIsInVybFByZWZpeCI6ImRlcm1hcnRzIiwidmVuZG9yIjoiZmhpcl9KcWdYYkBkZXJtYXJ0cyIsImlzcyI6Im1vZG1lZCIsInRva2VuVHlwZSI6ImFjY2VzcyIsImp0aSI6ImJkM2EwMWY4ZTA1NzRlOTFiMGIzMjQ5ZjRlNDFkN2RkIn0.t4kWVpIzkEAJvR12TZJvqVItPS5YlmTGKkgLgRKBD0s',
            }
        data = {}
        response = requests.post('https://stage.ema-api.com/ema-training/firm/dermarts/ema/fhir/v2/Binary', headers=headers, data=json.dumps(data))
        print(response.text)
        response_json = response.json()
        return response_json.get('issue')[0].get('details').get('text')
    
    def multiline_string_to_pdf(self, text):
        html_content = self.create_html(text)
        pdf_content = HTML(string=html_content).write_pdf()
        return pdf_content

    def create_html(self, text):
        lines = text.split('\n')
        html = "<body style='font-family:Arial; padding:20px;'>"
        html += "<h1 style='color: #333;'>Take care!</h1>"
        html += "<br/>"
        for line in lines:
            html += "<p style='text-indent: 50px; text-align: justify;'>" + line + "</p>"
            html += "<br/>"
        html += "</body>"
        return html


    def upload_document(self, s3_url, patient_instruction):
        # Step 2: Upload the document to the S3 URL
        document_data = self.multiline_string_to_pdf(patient_instruction)
        headers = {'Content-Type': 'application/pdf'}
        response = requests.put(s3_url, headers=headers, data=document_data)
        if response.status_code != 200:
            raise Exception('Failed to upload document to S3')
        return s3_url

    def post_document(self, s3_url, patient_id, document_title, file_name):
        # Step 3: Post the document to the DocumentReference resource
        data = {
            "resourceType": "DocumentReference",
            "status": "current",
            "type": {
                "text": "application/pdf"
            },
            "category": [
                {
                    "coding": [
                        {
                            "system": f"{self.base_url}/ValueSet/document-category",
                            "code": "7730",
                            "display": "External Visit Note"
                        }
                    ],
                    "text": "External Visit Note"
                }
            ],
            "subject": {
                "reference": f"Patient/{patient_id}",
                "display": f"Patient/{patient_id}"
            },
            "content": [
                {
                    "attachment": {
                        "title": document_title,
                        "contentType": "application/pdf",
                        "url": s3_url
                    }
                }
            ],
            "identifier": [
                {
                    "system": "filename",
                    "value": file_name
                }
            ]
        }
        self.call_api('DocumentReference', data)
    
    def create_patient_instruction_document(self, patient_id, patient_instruction, document_title, file_name):
        s3_url = self.get_s3_url()
        print("s3", s3_url)
        self.upload_document(s3_url, patient_instruction)
        self.post_document(s3_url, patient_id, document_title, file_name)

    # def get_last_three_visit_notes(self, patient_id):
    #     headers = {
    #     'Authorization': f'Bearer {self.bearer_token}',
    #     'Content-Type': 'application/fhir+json',
    #     'x-api-key': self.api_key
    #     }
    #     response = requests.get(f'{self.base_url}/DocumentReference?patient={patient_id}&category=note', headers=headers)
    #     response_data = response.json()
    #     print(response_data)
    #     if 'entry' in response_data:
    #         last_three_docs = response_data['entry'][-3:]
    #         last_three_visit_notes = []
    #         for doc in last_three_docs:
    #             visit_date = doc['resource']['date']
    #             pdf_url = doc['resource']['content'][0]['attachment']['url']
    #             pdf_response = requests.get(pdf_url)
    #             pdf_file = BytesIO(pdf_response.content)
    #             pdf_reader = PdfFileReader(pdf_file)
    #             # Assuming the PDF is text-based, not scanned/image-based
    #             doc_content = " ".join(page.extractText() for page in pdf_reader.pages)
    #             last_three_visit_notes.append((visit_date, doc_content))
    #         print(last_three_visit_notes)        
    #         return last_three_visit_notes

    



# patientId = "1121714"
# encounterId = "2496052"
# practitionerId = "1027882"

# # fhir_api = FHIRApi()
# # # fhir_api.post_to_fhir(transcription, patientId, encounterId, practitionerId, visit_note)
# # # fhir_api.create_patient_instruction_document(patientId, "transcription", "Take Care !!", "visit_note.pdf")
# # fhir_api.get_last_three_visit_notes(patientId)
# fhir_api = FHIRApi()
# patient_ids = fhir_api.get_patient_ids(practitionerId, "2022-12-12", "2022-12-12", "arrived")

# # Loop through each patient ID and get their name, then print it
# for patient_id in patient_ids:
#     patient_name = fhir_api.get_patient_name_by_id(patient_id)
#     print(patient_name)