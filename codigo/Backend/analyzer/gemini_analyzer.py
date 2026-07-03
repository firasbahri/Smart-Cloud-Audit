from analyzer.iLLM_analyzer import ILLMAnalyzer
from Model.vulnerability import Vulnerability
from google import genai
from dotenv import load_dotenv
import os
import json
import logging

logger=logging.getLogger(__name__)

class GeminiAnalyzer(ILLMAnalyzer):
  """Implementación de ILLMAnalyzer que usa la API de Google Gemini para el análisis con IA y la generación de comandos CLI."""

  def __init__(self):
    """Carga la API key desde .env y abre el cliente de Gemini. El listado de modelos es solo para depurar en consola."""
    load_dotenv()
    api_key=os.getenv("GEMINI_API_KEY")
    self.client=genai.Client(api_key=api_key)
    models = self.client.models.list()
    for model in models:
      print(model.name)

  def analyze(self, resources,vulnerabilities,userContext=dict):
    """Construye el prompt de auditoría, lo manda a Gemini y devuelve los hallazgos ya convertidos a Vulnerability.

    Args:
        resources: recursos escaneados de la cuenta (dict crudo, no el modelo de dominio).
        vulnerabilities: hallazgos del análisis estático, se incluyen en el prompt para que el modelo no los repita.
        userContext (dict): contexto de negocio aportado por el usuario (campos "company" y "resources").

    Returns:
        list[Vulnerability]: hallazgos adicionales que propone el modelo. Lista vacía si no encuentra nada nuevo.

    Example:
        >>> GeminiAnalyzer().analyze(scan_resources, static_vulns, {"company": "fintech con datos de clientes"})
        [Vulnerability(id="ai_001", severity="High", ...)]
    """
    try:
      prompt=self.build_analyze_prompt(resources, vulnerabilities, userContext)
      response = self.client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt
        )
      return self.parse_analyze_response(response.text)
    except Exception as e:
      logger.error(f"Error during Gemini analysis: {str(e)}")
      raise Exception(f"Error analyzing with Gemini : {str(e)}")


  def generate_recommendations(self, vulnerability):
    """Pide a Gemini los pasos de remediación y, si existe, el comando AWS CLI para arreglar una vulnerabilidad concreta.

    Args:
        vulnerability (Vulnerability): hallazgo sobre el que se quiere generar la solución.

    Returns:
        dict | None: {"recommendation": str, "cli_command": str} o None si el modelo no devuelve un comando válido.
    """
    try:
      prompt=self.build_generateCLI_prompt(vulnerability)
      response = self.client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt
        )
      return self.parse_generateCLI_response(response.text)
    except Exception as e:
      logger.error(f"Error during Gemini CLI generation: {str(e)}")
      raise Exception(f"Error generating CLI with Gemini : {str(e)}")


  def build_analyze_prompt(self, resources, vulnerabilities, userContext):
    """Arma el prompt de auditoría completo: contexto de negocio, recursos escaneados, vulnerabilidades ya
    detectadas y las instrucciones de formato/severidad que Gemini debe seguir para responder en JSON.

    Returns:
        str: prompt listo para mandar tal cual a generate_content.
    """
    if vulnerabilities:
        static_section = f"""VULNERABILITIES ALREADY DETECTED BY STATIC ANALYSIS (do not duplicate these):
{json.dumps(vulnerabilities, indent=2)}"""
        task_1 = "1. Analyze the static vulnerabilities in the company context — add business impact where relevant."
        task_2 = "2. Identify additional vulnerabilities not detected by static analysis (contextual, logical, or configuration-based)."
    else:
        static_section = """No static analysis has been performed yet for this account. Analyze the resources from scratch to identify security vulnerabilities, following AWS security best practices (CIS AWS Foundations Benchmark)."""
        task_1 = "1. Identify security vulnerabilities in the resources from scratch, following AWS security best practices (CIS AWS Foundations Benchmark)."
        task_2 = "2. Prioritize findings by exploitability and potential impact on the company."

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

{static_section}

---
YOUR TASKS:
{task_1}
{task_2}
3. Identify attack chains between resources (e.g., public S3 bucket + overpermissioned IAM role = lateral movement path).
4. For each vulnerability, explain the business impact using the company context
   provided — mention specifically how it affects THIS company (startup, developers,
   client data, etc.)
5. Prioritize vulnerabilities based on the company context — a startup with client
   data has different risk tolerance than an enterprise.

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
  def parse_analyze_response(self, response):
    """Limpia la respuesta de Gemini (a veces viene envuelta en \\`\\`\\`json ... \\`\\`\\`) y la convierte en
    una lista de Vulnerability.

    Args:
        response (str): texto crudo devuelto por response.text.

    Returns:
        list[Vulnerability]: vacía si el modelo respondió "[]".

    Raises:
        Exception: si el texto no es JSON válido tras quitar el markdown — normalmente indica que el modelo
            no siguió el formato pedido.
    """
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
          )
        )
      return vulnerabilities
    except Exception as e :
      logger.error("error during parsing the response")
      raise Exception(f"Error during parsing the response : {str(e)}")



  def build_generateCLI_prompt(self, vulnerability : Vulnerability):
    """Prompt corto y específico: dado un único hallazgo, pide la recomendación paso a paso y el comando CLI exacto.

    Returns:
        str: prompt para generate_content, pensado para una sola vulnerabilidad (no un batch).
    """

    return f"""Para la siguiente vulnerabilidad AWS genera:
1. Una recomendación clara de cómo remediarla
2. El comando AWS CLI exacto si existe

Vulnerabilidad: {vulnerability.name}
Recurso ID: {vulnerability.resource_id}
Tipo: {vulnerability.resource_type}

Responde SOLO en JSON:
{{
    "recommendation": "pasos claros para remediar enumerados como 1, 2, 3 , cada linea un paso separados por salto de linea",
    "cli_command": "comando AWS CLI exacto o null"
}}
"""

  def parse_generateCLI_response(self, response):
    """Igual que parse_analyze_response pero para la respuesta de generateCLI: quita el bloque de código si lo
    hay y valida que venga tanto el comando como la recomendación.

    Args:
        response (str): texto crudo de Gemini.

    Returns:
        dict | None: {"cli_command": str, "recommendation": str}. None si el modelo dice que no hay comando
            (cli_command es null/vacío) o si falta la recomendación.
    """
    try:
      text_received = response.strip()
      if text_received.startswith("```"):
        text_received = text_received.split("```")[1]
        # strip language tag (json, bash, etc.)
        first_newline = text_received.find("\n")
        if first_newline != -1:
          text_received = text_received[first_newline:].strip()

      parsed = json.loads(text_received)
      cmd = parsed.get("cli_command")
      recommendation = parsed.get("recommendation")
      if not cmd or str(cmd).lower() == "null":
        return None
      if not recommendation:
        logger.warning("CLI command provided without recommendation")
        return None
      return {
        "cli_command": cmd,
        "recommendation": recommendation
      }
    except Exception as e:
      logger.error("error during parsing the CLI response")
      raise Exception(f"Error during parsing the CLI response : {str(e)}")
