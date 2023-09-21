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
            "description": "ICD 10 codes, only from given list"
          },
          "ICD_10_code_display_name": {
            "type": "string",
            "description": "ICD 10 code description/display name"
          }
        },
        "required": ["ICD_10_code", "ICD_10_code_display_name"]
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
            "description": "CPT code applicabale to service offered in this encounter, only from given list"
          },
          "CPT_code_display_name": {
            "type": "string",
            "description": "CPT code description/display name"
          },
          "reason": {
            "type": "string",
            "description": "What service offered in the encounter for this code to be applicable?"
          },
          "associated_ICD_10_codes": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "ICD_10_code": {
                  "type": "string",
                  "description": "ICD 10 codes, only from given list"
                },
                "ICD_10_code_display_name": {
                  "type": "string",
                  "description": "ICD 10 code description/display name"
                }
              }
            }
          }
        },
        "required": ["CPT_code", "CPT_code_display_name","reason", "associated_ICD_10_codes"]
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
          "description": "E/M code, either for new patients (99202-99205) or established patients (99212-99215)"
        },
        "EM_code_display_name": {
          "type": "string",
          "description": "E/M code description/display name"
        },
        "reason": {
          "type": "string",
          "description": "Why does this E/M code apply?"
        },
        "associated_ICD_10_codes": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "ICD_10_code": {
                "type": "string",
                "description": "ICD 10 codes, only from a given list"
              },
              "ICD_10_code_display_name": {
                "type": "string",
                "description": "ICD 10 code description/display name"
              },
              "ICD_10_code_reason": {
                "type": "string",
                "description": "How does this ICD 10 code contributed to decision making of deciding E/M code"
              }
            }
          }
        }
      },
      "required": ["EM_code", "EM_code_display_name", "reason", "associated_ICD_10_codes"]
    }
  },
  "required": ["EM_code_data"]
}


icd_instruction = """
You are a helpful assistant which thinks step by step to find out icd codes applied to a outpatient encounter. You get encounter transcription as input.
You only use icd codes from below list. Act as certified dermatology medical coding expert, think step wise step and output a detailed list of icd codes associated with this encounter.
Before outputting the response, review and discard codes which doesn't exist in the given list. if no code matches, output empty strings.
Include all revalent icd 10 codes for this encounter. Output in correct format.
transcription is in following text delimited by triple backticks.
transcription :```{transcription}```
icd codes is in following text delimited by triple backticks.
icd codes: ```{icdCodes}```
"""

cpt_instruction = """
You are a helpful assistant which thinks step wise step to find out cpt/procedural codes for service offered during a outpatient encounter. You will get patient encounter transcription as input.
You only use cpt codes from below list. Act as certified dermatology medical coding expert, think step wise step and find out list of cpt code with their appropriate diagnosis codes(icd-10 codes) from below icd-10 list for the encounter. There can be zero, one or multiple cpt codes and for each cpt code, there can be multiple icd codes. 
Before outputting the response, review and discard codes which doesn't exist in the given list or which service doesn't offered in the encounter. if no code matches, output empty strings.
Output in correct format. Make sure to remove any uncessary procedural which haven't been performed in this encounter.
transcription is in following text delimited by triple backticks.
transcription :```{transcription}```
cpt codes is in following text delimited by triple backticks.
cpt codes: ```{cptCodes}```
icd codes is in following text delimited by triple backticks.
icd codes: ```{icdCodes}```
"""

em_instruction = """
You are a helpful assistant which thinks step wise step to find out eE/M codes applied to a outpatient encounter. You get encounter transcription as input.
You use below E/M guidelines to find appropriate E/M for this encounter. Act as certified dermatology medical coding expert, think step wise step and find out E/M code for this encounter with appropriate diagnosis codes(icd-10 codes) from below icd-10 list for the encounter. 
Before outputting the response, carefully review step by step. This is a {patientType} patient, keep in mind when choosing E/M code.
Output in correct format.
transcription is in following text delimited by triple backticks.
transcription :```{transcription}```
E/M guidelines is in following text delimited by triple backticks.
E/M guidelines: ```{emGuidelines}```
icd codes is in following text delimited by triple backticks.
icd codes: ```{icdCodes}```
"""