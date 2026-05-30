
from datetime import datetime as DateTime
class AuditResult:
    def __init__(self,id, vulnerabilities,accountID,userID,resources,origin,userContext=None):
        self.id = id
        self.vulnerabilities = vulnerabilities
        self.accountID = accountID
        self.userID = userID
        self.resources = resources
        self.origin = origin
        self.userContext = userContext
        self.created_at = DateTime.now().isoformat()