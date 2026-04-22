from analyzer.iLLM_analyzer import ILLMAnalyzer
from Model.vulnerability import Vulnerability
from google import genai
from dotenv import load_dotenv
import os
import json
import logging

logger=logging.getLogger(__name__)

class GeminiAnalyzer(ILLMAnalyzer):

  def __init__(self):
    load_dotenv()
    api_key=os.getenv("GEMINI_API_KEY")
    self.client=genai.Client(api_key=api_key)
    models = self.client.models.list()
    for model in models:
      print(model.name)

  def analyze(self, resources,vulnerabilities,userContext=dict):
    try:
      prompt=self.build_prompt(resources, vulnerabilities, userContext)
      response = self.client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt
        )
      return self.parse_response(response.text)
    except Exception as e:
      logger.error(f"Error during Gemini analysis: {str(e)}")
      raise Exception(f"Error analyzing with Gemini : {str(e)}")
    

  def build_prompt(self, resources, vulnerabilities, userContext):
    return f"""
You are an expert AWS cloud security auditor. Your task is to analyze the provided AWS resources and context, then return a structured security assessment.

IMPORTANT: Respond ONLY with a valid JSON array. No explanations, no markdown, no text before or after the JSON.

---

COMPANY CONTEXT:
{userContext.get('company', 'No context provided')}

RESOURCE CONTEXT:
{json.dumps(userContext.get('resources', {}), indent=2)}

AWS RESOURCES SCANNED:
{json.dumps(resources, indent=2)}

VULNERABILITIES ALREADY DETECTED BY STATIC ANALYSIS (do not duplicate these):
{json.dumps(vulnerabilities, indent=2)}

---

YOUR TASKS:
1. Analyze the static vulnerabilities in the company context — add business impact where relevant.
2. Identify additional vulnerabilities not detected by static analysis (contextual, logical, or configuration-based).
3. Identify attack chains between resources (e.g., public S3 bucket + overpermissioned IAM role = lateral movement path).

SEVERITY CRITERIA:
- Critical: immediate exploitation risk, data exfiltration possible, no authentication required
- High: significant risk, exploitation requires minimal effort or conditions
- Medium: risk exists but exploitation requires specific conditions
- Low: minor risk or best practice deviation

OUTPUT FORMAT (JSON array, in Spanish):
[
    {{
        "id": "ai_001",
        "name": "nombre de la vulnerabilidad",
        "description": "descripción técnica clara y también explicación en lenguaje natural para el usuario",
        "severity": "Critical|High|Medium|Low",
        "resource_id": "recurso afectado",
        "resource_type": "IAM|EC2|S3",
        "recommendation": "acción concreta para remediar",
        "attack_chain": "descripción de cómo este hallazgo puede combinarse con otros (si aplica, sino null)",
        "origin": "AI Analysis"
    }}
]

If no additional vulnerabilities are found beyond the static analysis, return an empty array: []
"""

  def parse_response(self, response):
    try:
      text_received=response.strip()
      if text_received.startswith("```"):
          text_received=text_received.split("```")[1]
          if text_received.startswith("json"):
            text_received=text_received[4:]

      

      lista=json.loads(text_received)
      vulnerabilities=[]

      for item in lista:   
        vulnerabilities.append(
          Vulnerability(
            id=item.get("id"),
            name=item.get("name"),
            description=item.get("description"),
            severity=item.get("severity"),
            resource_id=item.get("resource_id"),
            resource_type=item.get("resource_type"),
            origin=item.get("origin")
          )
        )
      return vulnerabilities
    except Exception as e :
      logger.error("error during parsing the response")
      raise Exception(f"Error during parsing the response : {str(e)}")
