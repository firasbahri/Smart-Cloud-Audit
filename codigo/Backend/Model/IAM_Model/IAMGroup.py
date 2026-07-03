

from Model.resource import Resource
 
class IAMGroup(Resource):
  def __init__(self,id,name,service,region,Creation_date,users,managed_policies,inline_policies):
    super().__init__(id,name,service,region,Creation_date)
    self.users = users
    self.managed_policies = managed_policies
    self.inline_policies = inline_policies

  

