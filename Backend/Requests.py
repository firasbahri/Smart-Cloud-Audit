from pydantic import BaseModel
from typing import Optional

class ArnRequest(BaseModel):
  arn : str

class UserRegisterRequest(BaseModel):
  username: str
  email: str
  password: str
  

class UserLoginRequest(BaseModel):
  username: str
  password: str

class CloudAddRequest(BaseModel):
  name: str
  arn: str
  provider : str
  description: str

class CloudUpdateRequest(BaseModel):
  id: str
  name: Optional[str] = None
  description: Optional[str] = None

class CloudDeleteRequest(BaseModel):
  id: str


