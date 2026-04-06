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
        groups=resources.get("groups", [])
        try:
            permVuln = self.iamAnalyzer.check_user_permissions(users)
            if permVuln:
                self.vulnerabilities.extend(permVuln)
            mfaVuln = self.iamAnalyzer.check_mfa(users)
            if mfaVuln:
                self.vulnerabilities.extend(mfaVuln)
            inactiveVuln = self.iamAnalyzer.check_inactive_users(users)
            if inactiveVuln:
                self.vulnerabilities.extend(inactiveVuln)
            groupVuln = self.iamAnalyzer.check_group_permissions(groups)
            if groupVuln:
                self.vulnerabilities.extend(groupVuln)

            logger.info(f"Completed analysis of AWS resources. Found {len(self.vulnerabilities)} vulnerabilities {self.vulnerabilities}.")
        except Exception as e:
            logger.error(f"Error occurred while analyzing AWS resources: {e}")
            raise Exception(f"Error occurred while analyzing AWS resources: {e}")
        return self.vulnerabilities
        