from datetime import timedelta
from http import HTTPStatus
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Security, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

from app.dependencies import get_database
from app.models.auth_model import Token
from app.services.auth_service import create_access_token, get_current_user, get_password_hash, verify_password
from app.services.user_service import generate_employee_user_id, generate_manager_user_id

import os
from dotenv import load_dotenv

load_dotenv()
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()


@router.post("/login/")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db=Depends(get_database)
) -> Token:
    user = db["users"].find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if user["role"] == "Manager":
        scopes = ["manager"]
    else:
        scopes = ["employee"]

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, scopes=scopes, expires_delta=access_token_expires
    )
    return {'access_token': access_token, "token_type": "bearer"}


@router.post("/create_account/")
async def create_account(
        username: Annotated[str, Query(min_length=5, max_length=50)],
        email: EmailStr,
        password: Annotated[str, Query(min_length=6, max_length=100)],
        manager: bool = False,
        current_user=Security(get_current_user, scopes=["manager"]),
        db=Depends(get_database),
):

    # Kiểm tra xem username và email có tồn tại không
    existing_user = db["users"].find_one({
        "$or": [
            {"username": username},
            {"email": email}
        ]
    })

    if existing_user:
        if existing_user.get("username") == username:
            raise HTTPException(
                status_code=400, detail="Username already in use")
        if existing_user.get("email") == email:
            raise HTTPException(status_code=400, detail="Email already in use")

    # Tạo user_id mới tùy thuộc vào role
    if manager:  # Nếu tạo tài khoản Manager
        new_user_id = await generate_manager_user_id(db)
        role = "Manager"
        user = {
            "user_id": new_user_id,
            "role": role,
            "username": username,
            "password": get_password_hash(password),
            "first_name": "",
            "last_name": "",
            "address": "",
            "email": email,
            "phone_number": "",
            "gender": None
        }
    else:  # Nếu tạo tài khoản Employee
        new_user_id = await generate_employee_user_id(db)
        role = "Employee"
        user = {
            "user_id": new_user_id,
            "role": role,
            "username": username,
            "password": get_password_hash(password),
            "first_name": "",
            "last_name": "",
            "address": "",
            "email": email,
            "phone_number": "",
            "gender": None,
            "worked_shifts": [],  # Danh sách rỗng cho Employee
            # Lưu tên Manager tạo tài khoản
            "manager_username": current_user.username
        }

    # Chèn user vào MongoDB
    db["users"].insert_one(user)

    # Trả về thông báo thành công với mã trạng thái HTTP 201 Created
    return JSONResponse(
        status_code=HTTPStatus.CREATED,
        content={
            "msg": "User created successfully",
            "user_id": new_user_id
        }
    )
