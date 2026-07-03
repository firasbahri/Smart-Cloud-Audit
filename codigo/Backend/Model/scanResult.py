from datetime import datetime as Datetime

class ScanResult:
    def __init__(self, scan_id, arn,cloud_id,user_id,creation_at,resources=None,userContext=None):  
        self.scan_id = scan_id
        self.arn = arn
        self.cloudAccount_id = cloud_id
        self.user_id = user_id
        self.userContext = userContext or {}
        self.resources = resources if resources is not None else {
            "users": [],
            "groups": [],
            "roles": [],
            "buckets": [],
            "ec2": [],
        }
        self.errors = []
        self.progress = 0
        self.status = "Started"
        self.created_at = creation_at


    



    