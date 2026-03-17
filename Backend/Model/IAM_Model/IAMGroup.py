

from .IAM import IAM
 
class IAMGroup(IAM):
  def __init__(self,id,name,service,region,Creation_date,users,policies):
    super().__init__(id,name,service,region,Creation_date,policies)
    self.users = users

  

