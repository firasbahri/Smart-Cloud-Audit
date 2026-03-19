

from Model.resource import Resource
 
class IAMGroup(Resource):
  def __init__(self,id,name,service,region,Creation_date,users,policies):
    super().__init__(id,name,service,region,Creation_date,policies)
    self.users = users

  

