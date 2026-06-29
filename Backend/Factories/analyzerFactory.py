from analyzer.aws_analyzer import AWSAnalyzer
from analyzer.IAnalyzer import IAnalyzer
import logging

logger = logging.getLogger(__name__)

class AnalyzerFactory:
    """Centraliza la elección de qué analizador estático usar, según el proveedor cloud de la cuenta."""

    @staticmethod
    def create_analyzer(provider: str) -> IAnalyzer:
        """Devuelve el analizador estático que corresponde al proveedor.

        Args:
            provider (str): "AWS" es el único soportado por ahora.

        Returns:
            IAnalyzer: instancia nueva del analizador concreto.

        Raises:
            ValueError: si el proveedor no tiene analizador implementado.
        """
        if provider == "AWS":
            logger.error("Creating AWS analyzer")
            return AWSAnalyzer()
        else:
            logger.error(f"Unsupported provider: {provider}")
            raise ValueError(f"Unsupported provider: {provider}")
