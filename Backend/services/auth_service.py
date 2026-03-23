
from Repositories.userRepository import UserRepository
from Model.user import User
from passlib.hash import bcrypt
from fastapi import HTTPException
from tokenConfigure import create_access_token, verify_access_token
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.user_repository = UserRepository()

    async def register_user(self, username, password,email):
        hashed_password = bcrypt.hash(password)
        user_data=User(username,hashed_password,email)
        if await self.user_repository.find_user_by_username(username):
          raise HTTPException(status_code=400, detail="Username already exists")
        
        user = await self.user_repository.create_user(user_data )
        return user
        
    async def login_user(self, username, password):
        userFounded= await self.user_repository.find_user_by_username(username)
        if userFounded and bcrypt.verify(password, userFounded.password):
            token=create_access_token({"sub": userFounded.id})
            logger.info(f"Generated token for username: {username}")
            return token
        logger.warning(f"Failed login attempt for username: {username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")

       