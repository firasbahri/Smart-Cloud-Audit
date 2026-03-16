import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

secret_key = os.getenv("SECRET_KEY")
expiration_time = timedelta(hours=1)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + expiration_time
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt

def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None