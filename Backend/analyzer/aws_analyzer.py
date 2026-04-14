from analyzer.IAnalyzer import IAnalyzer
from analyzer.IAM_Analyzer import IAMAnalyzer
from analyzer.ec2_analyzer import EC2Analyzer
from analyzer.s3_analyzer import S3Analyzer
import logging

logger = logging.getLogger(__name__)


class AWSAnalyzer(IAnalyzer):
    def __init__(self):
        self.iamAnalyzer = IAMAnalyzer()
        self.ec2Analyzer = EC2Analyzer()
        self.s3Analyzer = S3Analyzer()

    def analyze(self, resources: dict):
        vulnerabilities = []
        users = resources.get("users", [])
        groups = resources.get("groups", [])
        instances = resources.get("ec2", [])
        buckets = resources.get("s3", [])
        roles = resources.get("roles", [])

        try:
            vulnerabilities.extend(self.iamAnalyzer.analyze(users, groups, roles))
            vulnerabilities.extend(self.ec2Analyzer.analyze(instances))
            vulnerabilities.extend(self.s3Analyzer.analyze(buckets))

            logger.info(f"Completed analysis. Found {len(vulnerabilities)} vulnerabilities.")
        except Exception as e:
            logger.error(f"Error analyzing AWS resources: {e}")
            raise

        return vulnerabilities
