

from typing import Optional

class User :
    def __init__(self,username : str, password: str, email: str,id:Optional[str]= None  ):
        self.id = id
        self.username = username
        self.email = email
        self.password = password


