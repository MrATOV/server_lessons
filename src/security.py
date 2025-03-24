from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import datetime
import jwt


import src.database.orm as ORM

SECRET_KEY="4815162342"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/users/login')

async def authenticate_user(email: str, password: str):
    user = await ORM.select_user(email)
    if user.compare_password(password):
        return user
    return None

def create_access_token(data:dict):
    to_encode = dict(filter(lambda item: item[0] in ['id', 'username', 'role'], data.items()))
    expire = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_user = {
            "username": payload.get('username'),
            "id": payload.get('id'),
            'role': payload.get('role')
        }
        if current_user is None:
            raise HTTPException(status_code=401, detail='Invalid authentication credentials')
        return current_user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail='Invalid authentication credentials')