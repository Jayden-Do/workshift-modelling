from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
import jwt
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from passlib.context import CryptContext

import os
from dotenv import load_dotenv

from app.dependencies import get_database
from app.models.auth_model import TokenData
from app.models.user_model import ClientUser

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# Mã hóa password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer cho việc xác thực token
scopes = {
    "manager": "manager access",
    "employee": "employee access",
}
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    scopes=scopes,
)


def create_access_token(data: dict, scopes: list, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"scopes": scopes})
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Hàm hash và verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_current_user(security_scopes: SecurityScopes, token: Annotated[str, Depends(oauth2_scheme)], db=Depends(get_database)) -> ClientUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = f'Bearer'

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes: list = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes)
    except jwt.InvalidTokenError:
        raise credentials_exception

    user_dict = db["users"].find_one(
        {"username": username},
        projection={"_id": 0, "password": 0}
    )

    if user_dict is None:
        raise credentials_exception

    user = ClientUser(**user_dict)

    print("Token data: ", token_data)
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user
