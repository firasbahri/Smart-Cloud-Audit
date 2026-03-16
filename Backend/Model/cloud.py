from typing import Optional


class Cloud :
  def __init__(self,name,provider,identifier,account_id,user_id,description : str,created_at : str,id : Optional[str]= None):
    self.name = name
    self.provider = provider
    self.identifier = identifier
    self.account_id = account_id
    self.user_id = user_id
    self.created_at = created_at
    self.description = description
    self.id=id 


    

