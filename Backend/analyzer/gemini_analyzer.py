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
        static_section = f"""VULNERABILITIES ALREADY DETECTED BY STATIC ANALYSIS (context only, do not repeat these as new findings):
{json.dumps(vulnerabilities, indent=2)}"""
        task_1 = "1. Use the static vulnerabilities above as context — they are already known. Your job is to go BEYOND them."
    else:
        logger.info("No static vulnerabilities found, asking Gemini to analyze from scratch.")
        static_section = """No static analysis has been performed yet for this account.

Perform a complete independent AWS security assessment.
Do not assume that only critical issues should be reported.

Review AWS resources systematically and identify each independent security weakness found.
Create separate findings for separate security issues instead of grouping multiple misconfigurations into a single finding.

Follow AWS security best practices and CIS AWS Foundations Benchmark where applicable."""
        task_1 = "1. Identify security vulnerabilities in the resources from scratch, following AWS security best practices (CIS AWS Foundations Benchmark)."

    return f"""
You are a senior AWS cloud security auditor with deep expertise in identity and access management, network exposure, and real-world attack techniques. You think like an attacker to find what a checklist-based scanner would miss.

IMPORTANT: Respond ONLY with a valid JSON array. No explanations, no markdown fences, no text before or after the JSON.

---

COMPANY CONTEXT:
{userContext.get('company', 'No context provided')}

RESOURCE CONTEXT (business notes per resource, provided by the user):
{json.dumps(userContext.get('resources', {}), indent=2)}

AWS RESOURCES SCANNED:
{json.dumps(resources, indent=2)}

{static_section}

---
YOUR ANALYSIS, in order of priority:

{task_1}

2. ATTACK CHAINS — this is your highest-value contribution. Look across ALL resources (IAM + EC2 + S3 together) for combinations where one weakness enables another: an exposed network port leading to a role with excessive permissions, a public bucket referenced by a role, credentials that unlock broader access, etc. A single finding of this kind is worth more than five isolated ones. When you find one, narrate it as a short attack story inside "description": what an attacker sees first, what they gain next, and what they ultimately control.

3. CONTEXTUAL BLIND SPOTS — things a rule-based scanner structurally cannot see: trust relationships with external AWS accounts, credential hygiene (multiple long-lived keys, unclear ownership), configurations that are technically compliant but risky given what THIS company actually stores there (use the RESOURCE CONTEXT above — a bucket holding client financial data is not the same risk as an empty test bucket).

4. BUSINESS FRAMING — for every finding, make the impact concrete for THIS company: name what would actually be lost or exposed (client data, production uptime, account takeover), not generic textbook consequences.

5. URGENCY — reserve this for the 1-2 findings that genuinely cannot wait (a realistic, ready-to-use attack path with a clear entry point). For those, and ONLY those, start the "description" with the literal text "Urgent action: " followed by a plain-language explanation a non-technical founder would understand. Do not use this for every Critical finding — it should stand out as rare.

6. SIGNAL OVER NOISE — if a resource's context marks it as non-productive (test, sandbox, development, no real data), do not generate findings about it. Focus entirely on what matters for this company's real exposure.

SEVERITY CRITERIA:
- Critical: immediate exploitation risk, data exfiltration possible, no authentication required
- High: significant risk, exploitation requires minimal effort or conditions
- Medium: risk exists but exploitation requires specific conditions
- Low: minor risk or best practice deviation

OUTPUT FORMAT (JSON array, in English). Use ONLY these exact fields — no others, no "origin", no "attack_chain", no extra keys:
[
    {{
        "id": "ai_001",
        "name": "short and concrete finding name (no unnecessary jargon in the title)",
        "description": "2-4 sentences: what is happening, why it matters for THIS company, and if applicable, the attack chain narrated step by step and/or the urgency prefix — all integrated in this single field",
        "severity": "Critical|High|Medium|Low",
        "resource_id": "affected resource",
        "resource_type": "IAM|EC2|S3",
        "recommendation": "one concrete, actionable step to remediate it"
    }}
]

Order the array with the most severe and most business-critical findings first.
If no additional findings are found beyond the static analysis, return an empty array: []
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

    return f"""For the following AWS vulnerability, generate:
1. A clear recommendation on how to remediate it
2. The exact AWS CLI command if one exists

Vulnerability: {vulnerability.name}
Resource ID: {vulnerability.resource_id}
Type: {vulnerability.resource_type}

Respond ONLY with valid JSON:
{{
    "recommendation": "clear remediation steps numbered as 1, 2, 3 — one step per line separated by newline",
    "cli_command": "exact AWS CLI command or null"
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
