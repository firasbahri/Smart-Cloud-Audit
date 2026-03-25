

class AuditResult:
    def __init__(self,id, vulnerabilities,accountID,created_at):
        self.id = id
        self.vulnerabilities = vulnerabilities
        self.accountID = accountID
        self.created_at = created_at