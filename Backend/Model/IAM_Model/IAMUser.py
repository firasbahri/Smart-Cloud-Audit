

from .IAM import IAM

class IAMUser(IAM):
  def __init__(self,id,description,service,region,groups,access_keys,date,policies,mfa_enabled):
    super().__init__(id,description,service,region,date,policies)
    self.access_keys = access_keys
    self.groups = groups
    self.mfa_enabled = mfa_enabled
  



  def get_access_keys(self):
    return self.access_keys
  
  def get_groups(self):
    return self.groups


    