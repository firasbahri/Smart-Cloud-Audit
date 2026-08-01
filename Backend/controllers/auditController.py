from Factories.analyzerFactory import AnalyzerFactory
from Factories.AIAnalyzerFactory import AIAnalyzerFactory
from Model.vulnerability import Vulnerability
import logging

logger=logging.getLogger(__name__)

_SENSITIVE_FIELDS = {"user_data", "tags", "access_keys"}


def sanitize_resources_for_ai(resources: dict) -> dict:
    """Return a copy of resources with sensitive fields stripped from every resource entry.

    Called by AuditController before dispatching to any AI analyzer, so the guarantee
    applies to all current and future AI providers without touching their implementations.

    Fields removed: user_data (startup scripts may contain hardcoded secrets),
    tags (internal labels may reveal environment or ownership metadata),
    access_keys (IAM key material must never reach an external API).

    To exclude a new sensitive field, add its key to _SENSITIVE_FIELDS above.

    Args:
        resources (dict): raw scan dict with category keys (ec2, users, groups, roles, buckets),
                          each holding a list of resource dicts as stored in MongoDB.

    Returns:
        dict: structurally identical copy with _SENSITIVE_FIELDS removed from every item.
    """
    sanitized = {}
    for category, items in resources.items():
        if isinstance(items, list):
            sanitized[category] = [
                {k: v for k, v in item.items() if k not in _SENSITIVE_FIELDS}
                if isinstance(item, dict) else item
                for item in items
            ]
        else:
            sanitized[category] = items
    return sanitized


class AuditController:
    """Capa fina entre los servicios y los analizadores: pide a la factory correspondiente el analizador
    adecuado y le pasa los datos, sin saber nada de boto3, Gemini ni del proveedor concreto."""
    ai_analyzer=None

    def staticAudit(self, resources,provider):
        """Ejecuta el análisis basado en reglas para un proveedor dado.

        Args:
            resources: recursos ya convertidos al modelo de dominio (dict con users/groups/roles/ec2/buckets para AWS).
            provider (str): proveedor cloud, usado por AnalyzerFactory para elegir el analizador ("AWS" hoy).

        Returns:
            list[Vulnerability]: hallazgos del analizador estático correspondiente.
        """
        try:
            analyzer = AnalyzerFactory.create_analyzer(provider)
            result = analyzer.analyze(resources)
            return result
        except Exception as e:
            logger.error(f"Error auditing cloud resources: {str(e)}")
            raise Exception(f"Error auditing cloud resources: {str(e)}")


    def aiAudit(self, resources, vulnerabilities, user_context, modelo):
        """Ejecuta el análisis con IA, pasando también lo que ya encontró el análisis estático para que el
        modelo no lo repita.

        Args:
            resources: recursos escaneados de la cuenta.
            vulnerabilities: hallazgos ya detectados por staticAudit.
            user_context (dict): contexto de negocio aportado por el usuario.
            modelo (str): modelo de IA a usar, usado por AIAnalyzerFactory ("Gemini" hoy).

        Returns:
            list[Vulnerability]: hallazgos adicionales propuestos por el modelo.
        """
        try:
            self.ai_analyzer = AIAnalyzerFactory.create_analyzer(modelo)
            safe_resources = sanitize_resources_for_ai(resources)
            logger.info(f"Sanitized resources for AI analysis: {safe_resources}")
            result = self.ai_analyzer.analyze(safe_resources, vulnerabilities, user_context)
            return result
        except Exception as e:
            logger.error(f"Error auditing cloud resources with AI: {str(e)}")
            raise Exception(f"Error auditing cloud resources with AI: {str(e)}")


    def generate_recomendations(self,vulnerability : Vulnerability,modelo:str):
        """Genera recomendaciones de mitigación para una vulnerabilidad concreta, usando el analizador estático
        correspondiente al proveedor de la vulnerabilidad.

        Args:
            vulnerability (Vulnerability): hallazgo para el que se quieren recomendaciones.

        Returns:
            list[str]: lista de recomendaciones de mitigación.
        """
        try:
            self.ai_analyzer = AIAnalyzerFactory.create_analyzer(modelo)
            result = self.ai_analyzer.generate_recommendations(vulnerability)
            return result
           
        except Exception as e:
            logger.error(f"Error generating recommendations for vulnerability {vulnerability.id}: {str(e)}")
            raise Exception(f"Error generating recommendations for vulnerability {vulnerability.id}: {str(e)}")

