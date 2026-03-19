from datetime import datetime as Datetime

class ScanResult:
    def __init__(self, scan_id, arn,cloud_id,user_id):
        self.scan_id = scan_id
        self.arn = arn
        self.cloudAccount_id = cloud_id
        self.user_id = user_id
        self.resources = {
            "users": [],
            "groups": [],
            "roles": [],
            "buckets": [],
            "ec2": []
        }
        self.created_at = Datetime.now()
        self.errors = []
        self.progress = 0
        self.status = "Started"


    def finish_scan(self, resources, errors):
        self.resources = resources
        self.errors = errors
        self.status = "Completed"
        self.porcentage = 100


    