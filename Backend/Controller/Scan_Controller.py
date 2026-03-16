
from Factories.ResourceFactory import ResourceFactory
from services.AwsScanner import AwsScanner
from services.JSONSerializer import JSONSerializer
from Model.scanResult import ScanResult
from uuid import uuid4

class ScanController:

  def __init__(self, arn):
    self.scan_service =  AwsScanner()
    self.arn = arn
    self.account_id = None

  def connect(self):
    try:
      account_id=self.scan_service.connect(self.arn)
      self.account_id = account_id
    except Exception as e:
      raise Exception(f"Error connecting to AWS: {str(e)}")
    
     
    return account_id

  def scan_users(self):
    users=[]
    try:
      usersIAM = self.scan_service.scan_users()
      users = ResourceFactory.create_users(usersIAM)
      return users
      
    except Exception as e:
      return {f"message : error while scanning users": str(e)}
      
      

  def scan_groups(self):
    try:
      groupsIAM = self.scan_service.scan_groups()
      groups = ResourceFactory.create_groups(groupsIAM)
      return groups 
    except Exception as e:
      return {f"message : error while scanning groups": str(e) }

  def scan_roles(self):
    try:
      roleIAM = self.scan_service.scan_roles()
      roles= ResourceFactory.create_roles(roleIAM)
      return roles
     
    except Exception as e:
      return {f"message : error while scanning roles": str(e) }

  def scan_ec2(self):
    try:
      ec2 = self.scan_service.scan_ec2()
      instances= ResourceFactory.create_ec2(ec2)
      return instances
  
    except Exception as e:
     return (f"Error escaneando EC2: {str(e)}")

  def scan_s3(self):
    try:
      s3 = self.scan_service.scan_s3()
      buckets= ResourceFactory.create_s3(s3)
      return buckets
    except Exception as e:
      return {f"message : error while scanning s3": str(e)}



    


    