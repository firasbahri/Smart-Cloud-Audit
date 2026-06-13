import resend
import os
from logging import getLogger
logger=getLogger(__name__)

resend.api_key = os.getenv("RESEND_API_KEY")

async def send_email(email: str, token: str):
    server_host = os.getenv("SERVER_HOST")
    logger.info(f"server_host: {server_host}")
    link = f"{server_host}/auth/verify-email?token={token}"
    body = f"""
        <h2>SmartAudit - Verificación de Email</h2>
        <p>Haz clic en el siguiente enlace para verificar tu email:</p>
        <a href='{link}'>Verificar Email</a>
    """

    resend.Emails.send({
        "from": os.getenv("MAIL_FROM"),
        "to": email,
        "subject": "SmartAudit - Email Verification",
        "html": body
    })


async def send_password_reset_email(email: str, token: str):
    frontend_host = os.getenv("BASE_URL")
    logger.info(f"frontend_host: {frontend_host}")
    link = f"{frontend_host}/reset-password?token={token}"
    body = f"""
        <h2>SmartAudit - Restablecimiento de Contraseña</h2>
        <p>Haz clic en el siguiente enlace para restablecer tu contraseña:</p>
        <a href='{link}'>Restablecer Contraseña</a>
    """

    resend.Emails.send({
        "from": os.getenv("MAIL_FROM"),
        "to": email,
        "subject": "SmartAudit - Password Reset",
        "html": body
    })