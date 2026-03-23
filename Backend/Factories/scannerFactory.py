from scanners.AwsScanner import AwsScanner
from scanners.IScanner import IScanner
import logging

logger = logging.getLogger(__name__)

class ScannerFactory:
    @staticmethod
    def create_scanner(provider: str) -> IScanner:
        if provider == "AWS":
            logger.error("Creating AWS scanner")
            return AwsScanner()
        else:
            logger.error(f"Unsupported provider: {provider}")
            raise ValueError(f"Unsupported provider: {provider}")
        