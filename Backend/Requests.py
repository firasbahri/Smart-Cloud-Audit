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
  regions: list

class CloudUpdateRequest(BaseModel):
  id: str
  name: Optional[str] = None
  description: Optional[str] = None
  regions: Optional[list] = None

class CloudDeleteRequest(BaseModel):
  id: str

class cloudAuditRequest(BaseModel):
  scan_id: str  


class CloudAIAuditRequest(BaseModel):
  audit_id: str
  scan_id: str
  user_context: dict



class ContextRequest(BaseModel):
    resource_id:str
    context : str
