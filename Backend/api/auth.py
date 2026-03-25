
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from services.auth_service import AuthService
from Requests   import  UserRegisterRequest, UserLoginRequest
import logging
logger=logging.getLogger(__name__)
auth_service = AuthService()
router = APIRouter()


@router.post("/register")
async def register(user: UserRegisterRequest):
    logger.info(f"Registrando usuario: {user.username}")
  
    try:
        user_id = await auth_service.register_user(user.username, user.password, user.email)
        return {"message": "Usuario registrado exitosamente", "user_id": user_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/login")
async def login(user: UserLoginRequest):
    try:
        token = await auth_service.login_user(user.username, user.password)
        return {"token": token}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="error al iniciar sesión")

@router.get("/verify-email")
async def verify_email(token: str):
    logger.info(f"Verificando email con token: {token}")
    try:
        result = await auth_service.verify_email(token)
        if result:
            return RedirectResponse(url="http://localhost:3000/login?verified=true")
        else:
            raise HTTPException(status_code=400, detail="Token de verificación inválido")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))