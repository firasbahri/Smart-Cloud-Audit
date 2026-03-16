
from fastapi import APIRouter, HTTPException
from services.auth_service import AuthService
from Requests   import  UserRegisterRequest, UserLoginRequest

auth_service = AuthService()
router = APIRouter()


@router.post("/register")
async def register(user: UserRegisterRequest):
  
    try:
        user_id = await auth_service.register_user(user.username, user.password, user.email)
        return {"message": "User registered successfully", "user_id": user_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/login")
async def login(user: UserLoginRequest):
    try:
        token = await auth_service.login_user(user.username, user.password)
        return {"message": "Login successful", "token": token}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    