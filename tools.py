from typing import Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from azureCognitiveSearch import getIcdCodes, getCptCodes

class ICD10CodeInput(BaseModel):
    """Inputs to query ICD10 code"""

    query: str = Field(description="query to search for ICD10 code")


class ICD10CodeTool(BaseTool):
    name = "get_icd10_codes"
    description = """
        Useful when you want to get ICD 10 codes for a Diseases. It returns three potential options, you need to choose the most revalent ones.
    
        """
    args_schema: Type[BaseModel] = ICD10CodeInput

    def _run(self, query: str):
        results = getIcdCodes(query)
        if not results:
            return "No relevant ICD10 code found."
        
        response = " ICD10 codes Options for this query:\n"
        for i, result in enumerate(results):
            response += f"{result['id']} - {result['Description']},\n"


        return response.strip(',')
    
    def _arun(self, query: str):
        throw("Not implemented")

class CptCodeInput(BaseModel):
    """Inputs to query ICD10 code"""

    query: str = Field(description="query to search for ICD10 code")

class CPTCodeTool(BaseTool):
    name = "get_CPT_codes"
    description = """
        To retrieve CPT codes for a particular medical procedure, please provide a detailed description of the procedure. Only submit one at a time. The system will suggest potential codes; select the one that best matches. If none suits you, please discard the suggestions. Use query as most potential display name for potential appropriate code. Note: Requests for EM CPT codes are not supported.        .               """
    args_schema: Type[BaseModel] = CptCodeInput

    def _run(self, query: str):
        results = getCptCodes(query)
        if not results:
            return "No relevant CPT code found."

        response = " CPT codes options for this query:\n"
        for i, result in enumerate(results):
            if result['id'] == 'G4000':
                continue
            response += f"{result['id']} - {result['Description']},\n"
            

        return response.strip(',')
    
    def _arun(self, query: str):
        throw("Not implemented")