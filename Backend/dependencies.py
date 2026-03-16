
from tokenConfigure import verify_access_token
from fastapi import HTTPException, Header


async def get_user_id_from_token(Authorization: str= Header(...)):
    token = Authorization.split(" ")[1]
    print("Received token in dependency: ", token)
    payload = verify_access_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id