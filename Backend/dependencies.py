
from tokenConfigure import verify_access_token
from fastapi import HTTPException, Header,Query
import logging

logger = logging.getLogger(__name__)


async def get_user_id_from_token(Authorization: str= Header(...)):

    token = Authorization.split(" ")[1]
    payload = verify_access_token(token)
    user_id = payload.get("user_id")
    if user_id is None:
        logger.warning("User ID not found in token payload")
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id

async def get_user_id_from_query_token(token: str = Query(...)):
    payload = verify_access_token(token)
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id