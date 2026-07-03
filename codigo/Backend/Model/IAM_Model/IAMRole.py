

from Model.resource import Resource

class IAMRole(Resource):
  def __init__(self,id,name,service,region,Creation_date,assume_role_policy,managed_policies,inline_policies,trusted_entities):
    super().__init__(id,name,service,region,Creation_date)
    self.assume_role_policy = assume_role_policy
    self.managed_policies = managed_policies
    self.inline_policies = inline_policies
    self.trusted_entities = trusted_entities


  def get_assume_role_policy(self):
    return self.assume_role_policy