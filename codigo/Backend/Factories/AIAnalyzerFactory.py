from analyzer.iLLM_analyzer import ILLMAnalyzer
from analyzer.gemini_analyzer import GeminiAnalyzer
import logging
logger = logging.getLogger(__name__)

class AIAnalyzerFactory:
    """Centraliza la elección de qué motor de IA usar para el análisis. Hoy solo existe Gemini, pero al estar
    detrás de ILLMAnalyzer, añadir OpenAI/Claude más adelante es solo sumar una rama aquí."""

    @staticmethod
    def create_analyzer(modelo: str) -> ILLMAnalyzer:
        """Devuelve el analizador de IA que corresponde al modelo pedido.

        Args:
            modelo (str): "Gemini" es el único soportado por ahora.

        Returns:
            ILLMAnalyzer: instancia nueva del analizador concreto.

        Raises:
            ValueError: si el modelo no tiene analizador implementado.
        """
        if modelo == "Gemini":
            logger.error("Creating GeminiAnalyzer instance")
            return GeminiAnalyzer()
        else:
            logger.error(f"Unsupported modelo: {modelo}")
            raise ValueError(f"Unsupported modelo: {modelo}")
