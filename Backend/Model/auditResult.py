

class AuditResult:
    def __init__(self,id, vulnerabilities,accountID,userID,created_at):
        self.id = id
        self.vulnerabilities = vulnerabilities
        self.accountID = accountID
        self.userID = userID
        self.created_at = created_at