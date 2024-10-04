from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Security, status
from fastapi.responses import JSONResponse

from app.dependencies import get_database
from app.models.table_model import AssignTable, ModifyHistory, RegisterTable, Shift
from app.models.user_model import ClientUser, ShiftForEmployee
from app.services.auth_service import get_current_user
from app.services.table_service import generate_table_id

router = APIRouter()


@router.post("/submit_register_table/")
async def submit_register_table(
    shifts: list[Shift],
    current_user: Annotated[ClientUser, Security(get_current_user, scopes=["employee"])],
    db=Depends(get_database)
):
    # Kiểm tra số lượng ca đăng ký
    if len(shifts) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must register at least 5 shifts."
        )

    # Kiểm tra tính duy nhất của các ca
    seen_shifts = set()
    for shift in shifts:
        shift_key = (shift.shift_name, shift.date)
        if shift_key in seen_shifts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate shifts found. Each shift must be unique by shift_name and date."
            )
        seen_shifts.add(shift_key)

    # Giả sử current_date có múi giờ (offset-aware datetime)
    current_date = datetime.now(timezone.utc)  # Có thể có timezone info

    # year_start là ngày đầu tiên của năm, giả sử không có múi giờ (offset-naive datetime)
    year_start = datetime(current_date.year, 1, 1)

    # Chuyển đổi current_date thành offset-naive để tránh lỗi
    current_date_naive = current_date.replace(tzinfo=None)

    # Tính số tuần kể từ đầu năm
    week_number = ((current_date_naive - year_start).days // 7) + 1

    # Kiểm tra xem register table đã tồn tại cho tuần này chưa
    existing_register = db["tables"].find_one({
        "table_type": "register",
        # Sử dụng week_number thay vì yêu cầu người dùng nhập
        "week": week_number,
        "user_details.username": current_user.username
    })
    if existing_register:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Register table for this week already exists."
        )

    # Tạo table_id mới cho register table (dạng TRxxx)
    table_id = generate_table_id(db, "register")

    # Chuyển đổi các đối tượng Shift thành dictionary
    shifts_dict = [shift.model_dump() for shift in shifts]

    # Xây dựng dữ liệu cho register table
    register_table = {
        "table_id": table_id,
        "table_type": "register",
        "week": week_number,  # Tự động thêm tuần
        "date": current_date,  # Tự động thêm ngày hiện tại
        "user_details": {
            "user_id": current_user.user_id,
            "username": current_user.username
        },
        "shifts": shifts_dict
    }

    # Chèn register table vào MongoDB
    db["tables"].insert_one(register_table)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "msg": "Register table submitted successfully",
            "table_id": table_id
        }
    )


@router.get("/week_register_tables/")
async def get_register_tables_by_week(
    current_user: Annotated[ClientUser, Security(get_current_user, scopes=["manager"])],
    db=Depends(get_database)
):
    # Giả sử current_date có múi giờ (offset-aware datetime)
    current_date = datetime.now(timezone.utc)  # Có thể có timezone info

    # year_start là ngày đầu tiên của năm, giả sử không có múi giờ (offset-naive datetime)
    year_start = datetime(current_date.year, 1, 1)

    # Chuyển đổi current_date thành offset-naive để tránh lỗi
    current_date_naive = current_date.replace(tzinfo=None)

    # Tính số tuần kể từ đầu năm
    week_number = ((current_date_naive - year_start).days // 7) + 1
    register_tables = db["tables"].find({
        "table_type": "register",
        "week": week_number
    })

    result = []
    for register_table in register_tables:
        result.append(RegisterTable(**register_table))

    return result


@router.post("/approve_assign_table/")
async def approve_assign_table(
    shifts: list[Shift],
    current_user: Annotated[ClientUser, Security(get_current_user, scopes=["manager"])],
    db=Depends(get_database)
):
    # Tạo table_id mới cho assign table
    table_id = generate_table_id(db, "assign")

    # Giả sử current_date có múi giờ (offset-aware datetime)
    current_date = datetime.now(timezone.utc)  # Có thể có timezone info

    # year_start là ngày đầu tiên của năm, giả sử không có múi giờ (offset-naive datetime)
    year_start = datetime(current_date.year, 1, 1)

    # Chuyển đổi current_date thành offset-naive để tránh lỗi
    current_date_naive = current_date.replace(tzinfo=None)

    # Tính số tuần kể từ đầu năm
    week_number = ((current_date_naive - year_start).days // 7) + 1

    # Danh sách username từ shifts
    employee_usernames = []
    shifts_with_status = []

    for shift in shifts:
        # Thêm trường status vào shift
        shift_dict = shift.model_dump()
        shift_dict["status"] = "undone"
        shifts_with_status.append(shift_dict)

        if shift.username not in employee_usernames:
            employee_usernames.append(shift.username)

    # Xây dựng dữ liệu cho assign table
    assign_table = {
        "table_id": table_id,
        "table_type": "assign",
        "week": week_number,
        "date": current_date,
        "user_details": {
            "user_id": current_user.user_id,
            "username": current_user.username
        },
        "shifts": shifts_with_status,
        "employee_usernames": employee_usernames
    }

    try:
        # Chèn assign table vào MongoDB
        db["tables"].insert_one(assign_table)
        return {"status": "success", "table_id": table_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error inserting document: {str(e)}"
        )


@router.get("/assign_table_me/{week_number}/")
async def get_personal_assign_table_for_week(
    week_number: int,
    current_user: Annotated[ClientUser, Security(get_current_user, scopes=["employee"])],
    db=Depends(get_database)
):
    # Fetch the assign table for the given week
    assign_table = db["tables"].find_one(
        {
            "table_type": "assign",
            "week": week_number
        }
    )

    if not assign_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assign table not found for the given week."
        )

    # Filter shifts by the current user's username
    filtered_shifts = [
        shift for shift in assign_table.get("shifts", [])
        if shift["username"] == current_user.username
    ]

    # Return the assign table with only the filtered shifts
    return {
        "table_id": assign_table.get("table_id"),
        "table_type": assign_table.get("table_type"),
        "week": assign_table.get("week"),
        "date": assign_table.get("date"),
        "user_details": assign_table.get("user_details"),
        "shifts": filtered_shifts
    }


@router.get("/assign_table/{week_number}/")
async def get_general_assign_table_for_week(
    week_number: int,
    current_user: Annotated[ClientUser, Security(get_current_user, scopes=["manager"])],
    db=Depends(get_database)
):
    # Fetch the assign table for the given week
    assign_table = db["tables"].find_one(
        {
            "table_type": "assign",
            "week": week_number
        }
    )

    if not assign_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assign table not found for the given week."
        )

    # Return the complete assign table data
    return {
        "table_id": assign_table.get("table_id"),
        "table_type": assign_table.get("table_type"),
        "week": assign_table.get("week"),
        "date": assign_table.get("date"),
        "user_details": assign_table.get("user_details"),
        "shifts": assign_table.get("shifts"),
        "employee_usernames": assign_table.get("employee_usernames")
    }


@router.patch("/modify_assign/{week}/{modify_type}/")
async def modify_assign(
    current_user: Annotated[ClientUser, Security(get_current_user, scopes=["manager"])],
    week: int,
    modify_type: str = Path(..., regex="^(add|swap|pass)$"),
    # Use Body(...) to specify required data
    shift_data: list[Shift] = Body(...),
    new_username: str = Body(None),  # Optional for 'pass' operation
    db=Depends(get_database)
):
    # Validate modify_type
    if modify_type not in {"add", "swap", "pass"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid modify_type. Must be 'add', 'swap', or 'pass'."
        )

    # Fetch the assign table for the given week
    assign_table = db["tables"].find_one({
        "table_type": "assign",
        "week": week
    })

    if not assign_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assign table for this week not found."
        )

    assign_table_model = AssignTable(**assign_table)

    if modify_type == "add":
        for shift in shift_data:
            # Check if the shift already exists in the assign table
            if any(s.shift_name == shift.shift_name and s.date == shift.date and s.username == shift.username for s in assign_table_model.shifts):
                continue  # Skip adding this shift if it already exists

            # Set status to "undone" for new shifts
            shift_dict = shift.model_dump()
            shift_dict['status'] = "undone"
            assign_table_model.shifts.append(shift_dict)

            # Add username to the list if it's not already present
            if shift.username not in assign_table_model.employee_usernames:
                assign_table_model.employee_usernames.append(shift.username)

        modify_description = f"Added shift for employee: {shift_data[0].username} - Shift: {shift_data[0].shift_name} on {shift_data[0].date}"
        assign_table_model.modify_history.append(
            ModifyHistory(modify_type="add", description=modify_description)
        )

    elif modify_type == "swap":
        if len(shift_data) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="For 'swap', exactly 2 shifts are required."
            )

        shift_out, shift_in = shift_data

        # Check if any of the shifts to be swapped has status "done"
        for shift in [shift_out, shift_in]:
            existing_shift = next((s for s in assign_table_model.shifts
                                   if s.shift_name == shift.shift_name and s.date == shift.date and s.username == shift.username), None)
            if existing_shift and existing_shift.status == 'done':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot swap shifts where one of the shifts has already been completed (status: 'done')."
                )

        # Find and swap the shifts in the assign table
        for shift in assign_table_model.shifts:
            if shift.shift_name == shift_out.shift_name and shift.date == shift_out.date:
                shift.username = shift_in.username
            elif shift.shift_name == shift_in.shift_name and shift.date == shift_in.date:
                shift.username = shift_out.username

        # Update the assign table with the swapped shifts
        db["tables"].update_one(
            {"table_id": assign_table_model.table_id},
            {"$set": {"shifts": [s.model_dump()
                                 for s in assign_table_model.shifts]}}
        )

        modify_description = f"Swapped shift from {shift_out.username} to {shift_in.username} for shift {shift_in.shift_name} on {shift_in.date}"
        assign_table_model.modify_history.append(
            ModifyHistory(modify_type="swap", description=modify_description)
        )

    elif modify_type == "pass":
        if len(shift_data) != 1 or not new_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="For 'pass', exactly 1 shift and new username are required."
            )

        shift_to_pass = shift_data[0]

        # Update shift
        for shift in assign_table_model.shifts:
            if shift.shift_name == shift_to_pass.shift_name and shift.date == shift_to_pass.date and shift.username == shift_to_pass.username:
                shift.username = new_username
                if new_username not in assign_table_model.employee_usernames:
                    assign_table_model.employee_usernames.append(new_username)
                break

        modify_description = f"Passed shift {shift_to_pass.shift_name} on {shift_to_pass.date} from {shift_to_pass.username} to {new_username}"
        assign_table_model.modify_history.append(
            ModifyHistory(modify_type="pass", description=modify_description)
        )

    # Update the database
    db["tables"].update_one(
        {"table_id": assign_table_model.table_id},
        {"$set": assign_table_model.model_dump()}
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"msg": "Assign table updated successfully"}
    )


@router.post("/approve_worked_shifts/")
async def approve_worked_shifts(
    # List of shifts employee completed
    shifts_to_approve: list[ShiftForEmployee],
    current_user: Annotated[ClientUser, Security(get_current_user, scopes=["manager"])],
    db=Depends(get_database)
):
    current_date = datetime.now(timezone.utc)
    # Chuyển đổi current_date thành offset-naive để tránh lỗi
    current_date_naive = current_date.replace(tzinfo=None)

    for shift in shifts_to_approve:
        # Validate shift date
        if shift.date > current_date_naive:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve future shifts for date: {shift.date}"
            )

        # Update assign table: find the shift and mark it as 'done'
        result = db["tables"].update_one(
            {
                "table_type": "assign",
                "shifts.shift_name": shift.shift_name,
                "shifts.date": shift.date
            },
            {
                "$set": {"shifts.$.status": "done"}
            }
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shift not found for {shift.shift_name} on {shift.date}"
            )

        # Add shift to employee's worked_shifts
        db["users"].update_one(
            {"username": shift.username},
            {
                "$push": {
                    "worked_shifts": {
                        "shift_name": shift.shift_name,
                        "date": shift.date,
                    }
                }
            }
        )

    return {"status": "success", "message": "Shifts approved and recorded as 'done'."}
