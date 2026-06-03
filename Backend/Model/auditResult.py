
from datetime import datetime as DateTime
class AuditResult:
    def __init__(self,id, vulnerabilities,accountID,userID,resources,origin,counts:dict,userContext=None):
        self.id = id
        self.vulnerabilities = vulnerabilities
        self.accountID = accountID
        self.userID = userID
        self.resources = resources
        self.counts = counts or {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        self.origin = origin 
        self.userContext = userContext
        self.created_at = DateTime.now().isoformat()