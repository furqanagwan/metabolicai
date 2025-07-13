import os
from fastapi import Header, HTTPException, Depends

API_KEY = os.environ.get("API_KEY", "changeme")


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


def get_user_id(x_user_id: str = Header(...)):
    if not x_user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-Id header")
    return x_user_id
