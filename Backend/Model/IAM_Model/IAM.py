

from ..resource import Resource

class IAM (Resource):
  def __init__(self,id,description,service,region,Creation_date,policies):
    super().__init__(id,description,service,region,Creation_date)
    self.policies = policies

  def add_policy(self,policy):
    self.policies.append(policy)

  def get_policies(self):
    return self.policies
  
  def remove_policy(self,policy):
    self.policies.remove(policy)


