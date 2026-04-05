
from datetime import datetime as DateTime
class AuditResult:
    def __init__(self,id, vulnerabilities,accountID,userID):
        self.id = id
        self.vulnerabilities = vulnerabilities
        self.accountID = accountID
        self.userID = userID
        self.created_at = DateTime.now().isoformat()