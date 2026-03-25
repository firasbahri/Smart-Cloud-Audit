

from Model.resource import Resource

class IAMUser(Resource):
  def __init__(self,id,name,service,region,groups,access_keys,date,policies,mfa_enabled,password_last_used):
    super().__init__(id,name,service,region,date,policies)
    self.access_keys = access_keys
    self.groups = groups
    self.mfa_enabled = mfa_enabled
    self.password_last_used = password_last_used
  



  def get_access_keys(self):
    return self.access_keys
  
  def get_groups(self):
    return self.groups

  def get_Policies(self):
    return self.policies

    