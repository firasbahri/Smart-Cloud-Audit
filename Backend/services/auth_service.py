from Repositories.userRepository import UserRepository
from Model.user import User
from passlib.hash import bcrypt
from fastapi import HTTPException
from tokenConfigure import create_access_token
from services.email_service import send_email
import logging
import secrets

logger = logging.getLogger(__name__)
class AuthService:
    def __init__(self):
        self.user_repository = UserRepository()

    async def register_user(self, username, password, email):
        hashed_password = bcrypt.hash(password)
        token = secrets.token_hex(16)
        user_data = User(username, hashed_password, email, False, token)
        if await self.user_repository.find_user_by_username(username):
            raise HTTPException(status_code=400, detail="Username already exists")
        
        user = await self.user_repository.create(user_data)
        await send_email(email, token)
        return user
        
    async def login_user(self, username, password):
        try:
            userFounded= await self.user_repository.find_user_by_username(username)
            if not (userFounded and bcrypt.verify(password, userFounded.password)):
                logger.warning("invalid username or password for username: %s", username)
                raise HTTPException(status_code=401, detail="Invalid username or password")
            logger.info(
                "Login attempt for username: %s, email verified: %s",
                username,
                userFounded.isVerified,
            )
            if not userFounded.isVerified:
                raise HTTPException(status_code=403, detail="Email not verified")
            logger.info("userId es %s",userFounded.id)
            access_token = create_access_token({"user_id": userFounded.id})
            logger.info("token created for username: %s es %s", username, access_token)
            return access_token
        except HTTPException:
            raise   
        except Exception as e:
            logger.error("Error during login for username: %s - %s", username, str(e))
            raise HTTPException(status_code=500, detail="Error during login") from e
        

    async def verify_email(self, token):
        user = await self.user_repository.find_user_by_token(token)
        if user:
            user.verify_email()
            print("verification camp", user.isVerified)
            print(f"User {user.username} email verified.")
            await self.user_repository.update(user.id, user)
            return True
        return False