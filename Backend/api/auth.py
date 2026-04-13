from dotenv import load_dotenv
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from services.auth_service import AuthService
from Requests   import  UserRegisterRequest, UserLoginRequest
from Responses import UserResponse, TokenResponse
import logging
logger=logging.getLogger(__name__)
auth_service = AuthService()
router = APIRouter()
load_dotenv

@router.post("/register", response_model=UserResponse)
async def register(user: UserRegisterRequest):
    logger.info(f"Registrando usuario: {user.username}")
  
    try:
        user_id = await auth_service.register_user(user.username, user.password, user.email)
        return UserResponse(id=user_id, username=user.username, email=user.email, isVerified=False)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/login", response_model=TokenResponse)
async def login(user: UserLoginRequest):
    try:
        token = await auth_service.login_user(user.username, user.password)
        return TokenResponse(token=token)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="error al iniciar sesión")

@router.get("/verify-email")
async def verify_email(token: str):
    baseUrl=os.getenv("BASE_URL")
    logger.info(f"Verificando email con token: {token}")
    try:
        result = await auth_service.verify_email(token)
        if result:
            return RedirectResponse(url=f"{baseUrl}/login?verified=true")
        else:
            raise HTTPException(status_code=400, detail="Token de verificación inválido")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))