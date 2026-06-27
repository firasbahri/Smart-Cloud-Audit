from analyzer.aws_analyzer import AWSAnalyzer
from analyzer.IAnalyzer import IAnalyzer
import logging

logger = logging.getLogger(__name__)

class AnalyzerFactory:
    @staticmethod
    def create_analyzer(provider: str) -> IAnalyzer:
        if provider == "AWS":
            logger.error("Creating AWS analyzer")
            return AWSAnalyzer()
        else:
            logger.error(f"Unsupported provider: {provider}")
            raise ValueError(f"Unsupported provider: {provider}")
        