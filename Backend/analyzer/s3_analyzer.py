import logging
from Model.vulnerability import Vulnerability

logger = logging.getLogger(__name__)


class S3Analyzer:
    def analyze(self, buckets: list) -> list:
        vulnerabilities = []
        return vulnerabilities
