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
        <h2>SmartAudit - Email Verification</h2>
        <p>Click the link below to verify your email address:</p>
        <a href='{link}'>Verify Email</a>
    """

    resend.Emails.send({
        "from": os.getenv("MAIL_FROM"),
        "to": email,
        "subject": "SmartAudit - Email Verification",
        "html": body
    })


async def send_password_reset_email(email: str, token: str, username: str):
    frontend_host = os.getenv("BASE_URL")
    logger.info(f"frontend_host: {frontend_host}")
    link = f"{frontend_host}/reset-password?token={token}"
    body = f"""
        <h2>SmartAudit - Password Reset</h2>
        <p>Hi {username},</p>
        <p>We received a request to reset your password. If you did not make this request, you can safely ignore this email.</p>
        <p>To reset your password, click the link below:</p>
        <a href='{link}'>Reset Password</a>
        <p>This link will expire in 30 minutes. If you cannot click the link, copy and paste the URL into your browser.</p>
        <p>Thanks,</p>
        <p>The SmartAudit team</p>
    """

    resend.Emails.send({
        "from": os.getenv("MAIL_FROM"),
        "to": email,
        "subject": "SmartAudit - Password Reset",
        "html": body
    })
