

from typing import Optional

class User :
    def __init__(self,username : str, password: str, email: str, isVerified: bool = False, token:Optional[str]= None,id:Optional[str]= None  ):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.VerificationToken = token
        self.isVerified = isVerified
        self.resetPasswordToken = None



    def verify_email(self):
        self.isVerified = True

    def set_reset_password_token(self, token):
        self.resetPasswordToken = token



