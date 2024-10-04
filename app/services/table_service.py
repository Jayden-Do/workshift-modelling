from pymongo import DESCENDING


def generate_table_id(db, table_type: str) -> str:
    # Đặt tiền tố cho table_id dựa trên loại bảng
    prefix = "TR" if table_type == "register" else "TA"

    # Aggregation pipeline để tìm table có table_id bắt đầu bằng tiền tố
    pipeline = [
        {
            "$match": {
                "table_id": {"$regex": f"^{prefix}\\d{{3}}$"}
            }
        },
        {
            "$sort": {"table_id": DESCENDING}  # Sắp xếp theo table_id giảm dần
        },
        {
            "$limit": 1  # Chỉ lấy table có table_id lớn nhất
        }
    ]

    result = list(db["tables"].aggregate(pipeline))

    if result:
        last_table_id = result[0]["table_id"]  # Lấy table_id cuối cùng
        # Lấy phần số của table_id (bỏ ký tự tiền tố)
        last_number = int(last_table_id[2:])
        new_number = last_number + 1  # Tăng số lên 1
    else:
        new_number = 1  # Nếu không tìm thấy table nào, bắt đầu từ T001

    # Format lại thành tiền tố và số mới
    new_table_id = f"{prefix}{new_number:03d}"
    return new_table_id
