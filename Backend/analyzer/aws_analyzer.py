from analyzer.IAnalyzer import IAnalyzer
from analyzer.IAM_Analyzer import IAMAnalyzer
import logging
logger = logging.getLogger(__name__)

class AWSAnalyzer(IAnalyzer):
    
    def __init__(self):
        self.vulnerabilities = []
        self.iamAnalyzer = IAMAnalyzer()

    def analyze(self,resources:list):
        self.vulnerabilities = []
        users=resources.get("users", [])
        try:
            PermVuln = self.iamAnalyzer.check_user_permissions(users)
            if PermVuln:
                self.vulnerabilities.extend(PermVuln)
            MFAVuln = self.iamAnalyzer.check_mfa(users)
            if MFAVuln:
                self.vulnerabilities.extend(MFAVuln)
            InactiveVuln = self.iamAnalyzer.check_inactive_users(users)
            if InactiveVuln:
                self.vulnerabilities.extend(InactiveVuln)
            logger.info(f"Completed analysis of AWS resources. Found {len(self.vulnerabilities)} vulnerabilities {self.vulnerabilities}.")
        except Exception as e:
            logger.error(f"Error occurred while analyzing AWS resources: {e}")
            raise Exception(f"Error occurred while analyzing AWS resources: {e}")
        return self.vulnerabilities
        