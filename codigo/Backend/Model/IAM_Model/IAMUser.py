

from Model.resource import Resource

class IAMUser(Resource):
  def __init__(self,id,name,service,region,access_keys,date,managed_policies,inline_policies,mfa_enabled,password_last_used):
    super().__init__(id,name,service,region,date)
    self.access_keys = access_keys
    self.managed_policies = managed_policies
    self.inline_policies = inline_policies
    self.mfa_enabled = mfa_enabled
    self.password_last_used = password_last_used

  def get_access_keys(self):
    return self.access_keys

    