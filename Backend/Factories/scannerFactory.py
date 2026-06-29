from scanners.AwsScanner import AwsScanner
from scanners.IScanner import IScanner
import logging

logger = logging.getLogger(__name__)

class ScannerFactory:
    """Centraliza la elección de qué IScanner concreto usar, según el proveedor cloud de la cuenta."""

    @staticmethod
    def create_scanner(provider: str) -> IScanner:
        """Devuelve el scanner que corresponde al proveedor.

        Args:
            provider (str): "AWS" es el único soportado por ahora; Azure/GCP se sumarían aquí.

        Returns:
            IScanner: instancia nueva del scanner concreto.

        Raises:
            ValueError: si el proveedor no tiene scanner implementado.
        """
        if provider == "AWS":
            logger.error("Creating AWS scanner")
            return AwsScanner()
        else:
            logger.error(f"Unsupported provider: {provider}")
            raise ValueError(f"Unsupported provider: {provider}")

