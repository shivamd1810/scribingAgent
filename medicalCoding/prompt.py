icd_json_schema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "ICD_10_codes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "ICD_10_code": {
            "type": "string",
            "description": "Specific ICD 10 code extracted from a predefined list for disease classification."
          },
          "ICD_10_code_display_name": {
            "type": "string",
            "description": "Descriptive name or phrase representing the associated ICD 10 code."
          },
          "reason": {
            "type": "string",
            "description": "Reason for selecting this ICD 10 code. Reference the transcription and quote relevant sections for justification."
          }
        },
        "required": ["ICD_10_code", "ICD_10_code_display_name", "reason"]
      }
    }
  },
  "required": ["ICD_10_codes"]
}


cpt_json_schema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "CPT_to_ICD_mapping": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "CPT_code": {
            "type": "string",
            "description": "Specific CPT code identifying services offered during the encounter, selected from a predefined list."
          },
          "CPT_code_display_name": {
            "type": "string",
            "description": "Descriptive name or phrase representing the associated CPT code."
          },
          "reason": {
            "type": "string",
            "description": "Must add reference to the transcription and quote relevant sections of transcription. Please reference the transcription and include relevant quotations as evidence."
          },
          "associated_ICD_10_codes": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "ICD_10_code": {
                  "type": "string",
                  "description": "ICD 10 code from a predefined list linked with the given CPT code."
                },
                "ICD_10_code_display_name": {
                  "type": "string",
                  "description": "Descriptive name or phrase for the associated ICD 10 code."
                },
                "ICD_10_code_reason": {
                  "type": "string",
                  "description": "Must reference to the transcription and quote relevant sections of transcription. Explanation detailing how the ICD 10 code influenced the CPT code choice."
                }
              }
            }
          }
        },
        "required": ["CPT_code", "CPT_code_display_name", "reason", "associated_ICD_10_codes"]
      }
    }
  },
  "required": ["CPT_to_ICD_mapping"]
}


em_code = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "EM_code_data": {
      "type": "object",
      "properties": {
        "EM_code": {
          "type": "string",
          "enum": ["99202", "99203", "99204", "99205", "99212", "99213", "99214", "99215"],
          "description": "Specific E/M code which can be assigned to either new patients (codes 99202-99205) or established patients (codes 99212-99215)."
        },
        "EM_code_display_name": {
          "type": "string",
          "description": "Descriptive name or phrase representing the chosen E/M code."
        },
        "reason": {
          "type": "string",
          "description": "Must reference to the transcription and quote relevant sections of transcription.Justification for the selection of this E/M code. Please reference the transcription and include relevant quotations as evidence."
        },
        "associated_ICD_10_codes": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "ICD_10_code": {
                "type": "string",
                "description": "Specific ICD 10 code from a predefined list that influenced the E/M code choice."
              },
              "ICD_10_code_display_name": {
                "type": "string",
                "description": "Descriptive name or phrase for the linked ICD 10 code."
              },
              "ICD_10_code_reason": {
                "type": "string",
                "description": "Must reference to the transcription and quote relevant sections of transcription.Explanation detailing how the ICD 10 code played a role in the E/M code determination. Reference the transcription and quote relevant sections for justification."
              }
            },
            "required": ["ICD_10_code", "ICD_10_code_display_name", "ICD_10_code_reason"]
          }
        }
      },
      "required": ["EM_code", "EM_code_display_name", "reason", "associated_ICD_10_codes"]
    }
  },
  "required": ["EM_code_data"]
}


icd_instruction = """
Using dermatology clinic outpatient encounter transcription provided, assist in determining the appropriate ICD codes that apply to this outpatient encounter. Here are some guidelines:

1. Act as a certified dermatology medical coding expert and think critically through each step.
2. Use only the ICD codes from the given list.
3. Review your selections carefully and discard any codes that aren't on the given list. If no matches are found, provide an empty response.
4. Always ensure that the codes selected are relevant to the encounter and presented in the correct format.
5. For clarity and justification, reference and quote specific portions of the transcription when providing reasoning for your selections.

Input transcription: ```{transcription}```
ICD codes to consider: ```{icdCodes}```
"""

cpt_instruction = """
Using dermatology clinic outpatient encounter transcription provided, help determine the CPT/procedural codes for services rendered during an outpatient encounter. Follow these guidelines:

1. Act as a certified dermatology medical coding expert and think critically through each step.
2. Only use CPT codes from the provided list. Must reference to the transcription and quote relevant sections of transcription in reason.
3. For each CPT code, there may be associated ICD codes. Be sure to link them appropriately.  Must reference to the transcription and quote relevant sections of transcription in reason.. 
4. Thoroughly review your selections, ensuring you discard any codes not on the given list or not relevant to the services described in the transcription. If no matches are found, provide an empty response.
5. Always ensure the codes are provided in the correct format.
6. For justification, reference and quote specific portions of the transcription when providing reasoning for your selections.

Input transcription: ```{transcription}```
CPT codes to consider: ```{cptCodes}```
ICD codes to consider: ```{icdCodes}```
"""

em_instruction = """
Using dermatology clinic outpatient encounter transcription provided, assist in selecting the correct E/M code for this outpatient encounter, keeping the following in mind:

1. Act as a certified dermatology medical coding expert and think critically through each step.
2. Use the provided E/M guidelines to determine the most suitable E/M code.
3. Keep the patient type (e.g., new or established) in mind when selecting an E/M code. Must reference to the transcription and quote relevant sections of transcription in reason.
4. Link the appropriate ICD-10 diagnosis codes from the given list for the encounter.
5. Review your selection carefully to ensure accuracy.
6. Always ensure the code is presented in the correct format.
7. For clarity and justification, reference and quote specific portions of the transcription when providing reasoning for your selections.

This is a {patientType} patient.
Input transcription: ```{transcription}```
E/M guidelines to consider: ```{emGuidelines}```
ICD codes to consider: ```{icdCodes}```
"""
