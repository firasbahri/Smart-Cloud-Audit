from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import  EmailStr
import os

conf=ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM = os.getenv("MAIL_FROM"),
    MAIL_PORT = 465,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True
)

async def send_email(email: EmailStr, token: str):
    server_host=os.getenv("SERVER_HOST")
    link= f"{server_host}/auth/verify-email?token={token}"
    body = f"Please click the following link to verify your email: <a href='{link}'>Verify Email</a>"
    subject="SmartAudit - Email Verification"
    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=body,
        subtype="plain"
    )
    fm = FastMail(conf)
    await fm.send_message(message)
