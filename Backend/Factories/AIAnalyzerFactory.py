from analyzer.iLLM_analyzer import ILLMAnalyzer
from analyzer.gemini_analyzer import GeminiAnalyzer
import logging
logger = logging.getLogger(__name__)

class AIAnalyzerFactory:
    @staticmethod
    def create_analyzer(modelo: str) -> ILLMAnalyzer:
        if modelo == "Gemini":
            logger.error("Creating GeminiAnalyzer instance")
            return GeminiAnalyzer()
        else:
            logger.error(f"Unsupported modelo: {modelo}")
            raise ValueError(f"Unsupported modelo: {modelo}")