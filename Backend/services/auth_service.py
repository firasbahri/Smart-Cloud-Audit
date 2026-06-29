from datetime import timedelta

from Repositories.userRepository import UserRepository
from Repositories.cloudRepository import CloudRepository
from services.cloudAuth_service import CloudAuthService
from Model.user import User
from passlib.hash import bcrypt
from fastapi import HTTPException
from tokenConfigure import create_access_token
from services.email_service import send_email, send_password_reset_email
import logging
import secrets

logger = logging.getLogger(__name__)
class AuthService:
    """Registro, login y gestión de cuenta de usuario (verificación de email, recuperación de contraseña, borrado)."""
    def __init__(self):
        self.user_repository = UserRepository()

    async def register_user(self, username, password, email):
        """Crea el usuario con la contraseña ya hasheada y un token de verificación, y dispara el email de
        verificación. El usuario queda como no verificado hasta que confirme ese email.

        Args:
            username (str): nombre de usuario, debe ser único.
            password (str): contraseña en texto plano (se hashea aquí con bcrypt antes de guardar nada).
            email (str): correo al que se manda el enlace de verificación.

        Returns:
            User: el usuario recién creado (con isVerified=False).

        Raises:
            HTTPException: 400 si el username ya existe.
        """
        hashed_password = bcrypt.hash(password)
        token = secrets.token_hex(16)
        user_data = User(username, hashed_password, email, False, token)
        if await self.user_repository.find_user_by_username(username):
            raise HTTPException(status_code=400, detail="Username already exists")

        user = await self.user_repository.create(user_data)
        await send_email(email, token)
        return user

    async def login_user(self, username, password):
        """Valida usuario/contraseña y, si la cuenta ya está verificada, devuelve un JWT válido 60 minutos.

        Args:
            username (str): nombre de usuario.
            password (str): contraseña en texto plano, se compara con el hash guardado vía bcrypt.verify.

        Returns:
            str: token de acceso (JWT) firmado, con user_id en el payload.

        Raises:
            HTTPException: 401 si el usuario no existe o la contraseña no coincide, 403 si el email aún no
                está verificado, 500 para cualquier otro error inesperado.
        """
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
            access_token = create_access_token({"user_id": userFounded.id}, expiration_delta=timedelta(minutes=60))
            logger.info("token created for username: %s es %s", username, access_token)
            return access_token
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error during login for username: %s - %s", username, str(e))
            raise HTTPException(status_code=500, detail="Error during login") from e


    async def verify_email(self, token):
        """Marca como verificado al usuario propietario del token recibido por email.

        Args:
            token (str): token de verificación generado en register_user.

        Returns:
            bool: True si se encontró y verificó un usuario con ese token, False si el token no es válido.
        """
        user = await self.user_repository.find_user_by_token(token)
        if user:
            user.verify_email()
            await self.user_repository.update(user.id, user)
            return True
        return False



    async def send_password_reset_email(self, email):
        """Genera un token de recuperación (válido 30 minutos), lo guarda en el usuario y manda el email con el enlace.

        Args:
            email (str): correo de la cuenta a recuperar.

        Raises:
            Exception: si no existe ningún usuario con ese email. Nota: el endpoint que llama a esto responde
                igual al usuario final tanto si existe como si no, por seguridad (no confirmar emails registrados).
        """
        user =await self.user_repository.find_user_by_email(email)
        if not user:
            raise Exception("No user found with that email")

        token = create_access_token({"user_id": user.id}, expiration_delta=timedelta(minutes=30))
        user.set_reset_password_token(token)
        await self.user_repository.update(user.id, user)
        await send_password_reset_email(email, token)



    async def reset_password(self, token, new_password):
        """Cambia la contraseña del usuario asociado al token de recuperación y consume el token (queda en None).

        Args:
            token (str): token recibido por email en send_password_reset_email.
            new_password (str): contraseña nueva en texto plano, se hashea antes de guardar.

        Returns:
            bool: True si se pudo cambiar.

        Raises:
            Exception: si el token no corresponde a ningún usuario (no existe o ya expiró/se usó).
        """
        user =await self.user_repository.find_user_by_password_reset_token(token)
        if not user:
            raise Exception("Invalid password reset token")

        user.password = bcrypt.hash(new_password)
        user.reset_password_token = None
        await self.user_repository.update(user.id, user)
        return True



    async def delete_account(self, user_id):
        """Borra la cuenta de usuario y, en cascada, todas sus cuentas cloud vinculadas (con sus escaneos y
        auditorías, vía CloudAuthService.delete_cloud_data) antes de borrar al propio usuario.

        Args:
            user_id (str): id del usuario a eliminar.

        Returns:
            bool: True si terminó sin errores.

        Raises:
            Exception: si no existe un usuario con ese id.
        """
        user = await self.user_repository.findById(user_id)
        if not user:
            raise Exception("User not found")
        cloudRepository = CloudRepository()
        cloud_service = CloudAuthService()
        cuentas = await cloudRepository.found_cloud_accounts(user_id)
        for cuenta in cuentas:
            logger.info("Deleting cloud data for user_id: %s, cloud_account_id: %s", user_id, cuenta.id)
            await cloud_service.delete_cloud_data(user_id, cuenta.id)
        await self.user_repository.delete(user_id)
        return True
