

from Model.resource import Resource

class IAMRole(Resource):
  def __init__(self,id,name,service,region,Creation_date,assume_role_policy,policies):
    super().__init__(id,name,service,region,Creation_date,policies)
    self.assume_role_policy = assume_role_policy

  def get_assume_role_policy(self):
    return self.assume_role_policy