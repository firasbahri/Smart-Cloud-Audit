from abc import ABC, abstractmethod


class ILLMAnalyzer(ABC):
    """Contrato para analizadores que usan un modelo de lenguaje (Gemini, y cualquier otro que se añada) en vez de reglas fijas."""

    @abstractmethod
    def analyze(self, resources,vulnerabilities,userContext=dict ):
        """Pide al modelo un análisis de seguridad contextualizado.

        Args:
            resources: recursos escaneados de la cuenta (forma cruda, tal cual los serializa el scan).
            vulnerabilities: hallazgos que ya detectó el análisis estático, para que el modelo no los repita.
            userContext (dict): descripción de negocio aportada por el usuario, usada para priorizar el riesgo.

        Returns:
            list[Vulnerability]: hallazgos adicionales propuestos por el modelo.
        """
        pass

    def build_analyze_prompt(self, resources, vulnerabilities, userContext):
        """Construye el prompt de texto que se envía al modelo para el análisis. Cada implementación define su propio formato."""
        pass

    def generate_recommendations(self, vulnerability):
        """Genera recomendaciones de mitigación para una vulnerabilidad concreta, usando el analizador correspondiente al proveedor de la vulnerabilidad y comando CLI."""
        pass
    def parse_analyze_response(self, response):
        """Convierte la respuesta en texto del modelo en una lista de objetos Vulnerability."""
        pass
