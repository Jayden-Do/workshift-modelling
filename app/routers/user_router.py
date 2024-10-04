from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Security

from app.dependencies import get_database
from app.models.user_model import ClientUser, Employee
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get("/me/")
async def get_me(
    current_user: Annotated[ClientUser, Security(
        get_current_user)],
):
    return current_user


@router.put("/me/update")
async def update_information(
    update_data: dict,
    current_user: Annotated[ClientUser, Depends(get_current_user)],
    db=Depends(get_database)
):
    # Chỉ cho phép Employee cập nhật các trường cá nhân như tên, địa chỉ, email,...
    allowed_fields = {"first_name", "last_name",
                      "address", "email", "phone_number", "gender"}

    # Lọc dữ liệu để chỉ cập nhật các trường được phép
    filtered_update_data = {k: v for k,
                            v in update_data.items() if k in allowed_fields}

    if not filtered_update_data:
        raise HTTPException(
            status_code=400, detail="No valid fields to update")

    # Cập nhật thông tin cho user hiện tại (dựa trên username)
    db["users"].update_one({"user_id": current_user.user_id}, {
                           "$set": filtered_update_data})

    # Trả về user đã được cập nhật
    updated_user = db["users"].find_one(
        {"user_id": current_user.user_id}, {"_id": 0, "password": 0})
    return {"msg": "Your information has been updated successfully", "user": updated_user}


@router.get("/me/done_shifts/")
async def get_done_shifts(
    current_user: Annotated[Employee, Security(get_current_user, scopes=["employee"])],
):
    return {"worked_shifts": current_user.worked_shifts}


@router.get("/all/", response_model=list[ClientUser])
async def get_all_users(current_user: Annotated[ClientUser, Security(
    get_current_user, scopes=["manager"]
)],
    db=Depends(get_database)
):
    user_list = db["users"].find(
        {"manager_username": current_user.username},
        projection={"_id": 0, "password": 0},
        sort={"user_id": -1}
    )
    return user_list


@router.put("/{user_id}/update")
async def update_user(
    user_id: str,
    update_data: dict,
    current_user: Annotated[ClientUser, Security(get_current_user, scopes=["manager"])],
    db=Depends(get_database)
):
    # Tìm user dựa vào user_id
    user = db["users"].find_one({"user_id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Cập nhật chỉ các trường được gửi trong update_data
    db["users"].update_one({"user_id": user_id}, {"$set": update_data})

    # Trả về user đã cập nhật
    updated_user = db["users"].find_one(
        {"user_id": user_id}, {"_id": 0, "password": 0})
    return {"msg": "User updated successfully", "user": updated_user}
