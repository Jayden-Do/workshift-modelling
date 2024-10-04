from fastapi import Depends
from pymongo import DESCENDING

from app.dependencies import get_database
from app.models.user_model import ClientUser
from app.services.auth_service import get_current_user


async def generate_employee_user_id(db):
    # Aggregation pipeline để tìm user có user_id bắt đầu bằng "E", sắp xếp theo user_id giảm dần
    pipeline = [
        {
            "$match": {
                # Lọc những user_id có format EXXX
                "user_id": {"$regex": "^E\\d{3}$"}
            }
        },
        {
            "$sort": {"user_id": DESCENDING}  # Sắp xếp theo user_id giảm dần
        },
        {
            "$limit": 1  # Chỉ lấy user có user_id lớn nhất
        }
    ]

    result = list(db["users"].aggregate(pipeline))

    if result:
        last_user_id = result[0]["user_id"]  # Lấy user_id cuối cùng
        # Lấy phần số của user_id (bỏ ký tự "E")
        last_number = int(last_user_id[1:])
        new_number = last_number + 1  # Tăng số lên 1
    else:
        new_number = 1  # Nếu không tìm thấy user nào, bắt đầu từ E001

    # Format lại thành EXXX
    new_user_id = f"E{new_number:03d}"
    return new_user_id


async def generate_manager_user_id(db):
    # Aggregation pipeline để tìm user có user_id bắt đầu bằng "M", sắp xếp theo user_id giảm dần
    pipeline = [
        {
            "$match": {
                # Lọc những user_id có format MXXX
                "user_id": {"$regex": "^M\\d{3}$"}
            }
        },
        {
            "$sort": {"user_id": DESCENDING}  # Sắp xếp theo user_id giảm dần
        },
        {
            "$limit": 1  # Chỉ lấy user có user_id lớn nhất
        }
    ]

    result = list(db["users"].aggregate(pipeline))

    if result:
        last_user_id = result[0]["user_id"]  # Lấy user_id cuối cùng
        # Lấy phần số của user_id (bỏ ký tự "M")
        last_number = int(last_user_id[1:])
        new_number = last_number + 1  # Tăng số lên 1
    else:
        new_number = 1  # Nếu không tìm thấy user nào, bắt đầu từ E001

    # Format lại thành EXXX
    new_user_id = f"M{new_number:03d}"
    return new_user_id
