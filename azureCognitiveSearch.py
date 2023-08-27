# Description: This file contains the functions to query the Azure Cognitive Search API
import openai
import base64
import streamlit as st

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import Vector


# Configure environment variables


openai.api_type = "azure"
openai.api_base = "https://medscribeai.openai.azure.com"
openai.api_version = "2023-05-15"
openai.api_key= st.secrets["AZURE_OPENAI_API_KEY"]





def generate_embeddings(text):
    response = openai.Embedding.create(
        input=text, engine="text-embedding-ada-002")
    embeddings = response['data'][0]['embedding']
    return embeddings
 

@st.cache_data
def getIcdCodes(query):
    icd10_search_client = SearchClient("https://icd10search.search.windows.net", "icd10", credential=AzureKeyCredential(st.secrets["ICD_10_CREDENTIAL"]))
    vector = Vector(value=generate_embeddings(query), k=3, fields="DescriptionVector")
    
    results = icd10_search_client.search(  
        search_text=None,  
        vectors= [vector],
        select=["id", "Description"],
        top=3
    )
    
    # List to store formatted results
    formatted_results = []

    for result in results:
        # Decode the ID
        decoded_id = decode_base64(result['id'])
        
        # Append the result to the new list
        formatted_results.append({
            'id': decoded_id,
            'Description': result['Description']
        })

    return formatted_results

@st.cache_data
def getCptCodes(query):
    cpt_search_client = SearchClient("https://cptcodesearch.search.windows.net", "cptcodesearch", credential=AzureKeyCredential(st.secrets["CPT_CODE_CREDENTIAL"]))
    vector = Vector(value=generate_embeddings(query), k=3, fields="DescriptionVector")
    
    results = cpt_search_client.search(  
        search_text=None,  
        vectors= [vector],
        select=["id", "Description"],
        top=3
    )
    
    # List to store formatted results
    formatted_results = []

    for result in results:
        # Decode the ID
        decoded_id = decode_base64(result['id'])

        # Append the result to the new list
        formatted_results.append({
            'id': decoded_id,
            'Description': result['Description']
        })

    return formatted_results



def decode_base64(encoded_str):
    '''Decodes a Base64 encoded string.'''
    return base64.b64decode(encoded_str).decode('utf-8')
