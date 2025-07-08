from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import datetime
import jwt
import os

SECRET_KEY=os.getenv("AUTH_SECRET_KEY")
ALGORITHM=os.getenv("AUTH_ALGORITHM")

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_user = {
            "username": payload.get('username'),
            "id": payload.get('id'),
            'role': payload.get('role'),
            'avatar': payload.get('avatar')
        }
        if current_user is None:
            raise HTTPException(status_code=401, detail='Invalid authentication credentials')
        return current_user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail='Invalid authentication credentials')