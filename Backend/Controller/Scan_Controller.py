
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
      usersFactory = ResourceFactory.create_users(usersIAM)
      users=JSONSerializer.serializeList(usersFactory)
      return users
      
    except Exception as e:
      return {f"message : error while scanning users": str(e)}
      
      

  def scan_groups(self):
    try:
      groupsIAM = self.scan_service.scan_groups()
      groupsFactory = ResourceFactory.create_groups(groupsIAM)
      groups=JSONSerializer.serializeList(groupsFactory)
      return groups 
    except Exception as e:
      return {f"message : error while scanning groups": str(e) }

  def scan_roles(self):
    try:
      roleIAM = self.scan_service.scan_roles()
      rolesFactory = ResourceFactory.create_roles(roleIAM)
      roles = JSONSerializer.serializeList(rolesFactory)
      return roles
     
    except Exception as e:
      return {f"message : error while scanning roles": str(e) }

  def scan_ec2(self):
    try:
      ec2 = self.scan_service.scan_ec2()
      instancesFactory= ResourceFactory.create_ec2(ec2)
      instances = JSONSerializer.serializeList(instancesFactory)
      return instances
  
    except Exception as e:
     return (f"Error escaneando EC2: {str(e)}")

  def scan_s3(self):
    try:
      s3 = self.scan_service.scan_s3()
      bucketsFactory= ResourceFactory.create_buckets(s3)
      buckets = JSONSerializer.serializeList(bucketsFactory)
      return buckets
    except Exception as e:
      return {f"message : error while scanning s3": str(e)}



    


    