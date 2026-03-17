from datetime import datetime as Datetime

class ScanResult:
    def __init__(self, scan_id, arn,cloud_id,user_id):
        self.scan_id = scan_id
        self.arn = arn
        self.cloudAccount_id = cloud_id
        self.user_id = user_id
        self.resources = {}
        self.created_at = Datetime.now()
        self.errors = []
        self.progress = 0
        self.status = "Started"





    def update_accountID(self,account_id):
        self.account_id=account_id

    def upddate_status(self, status):
        self.status = status

    def update_porcentage(self, porcentage):
        self.porcentage = porcentage

    def finish_scan(self, resources, errors):
        self.resources = resources
        self.errors = errors
        self.status = "Completed"
        self.porcentage = 100


    