from datetime import datetime
from pydantic import BaseModel


class Shift(BaseModel):
    shift_name: str
    date: datetime
    duration: str
    username: str


class ShiftForAssign(Shift):
    status: str | None = "undone"


class UserDetails(BaseModel):
    user_id: str
    username: str


class Table(BaseModel):
    table_id: str
    table_type: str
    week: int
    date: datetime
    user_details: UserDetails
    shifts: list[Shift]


class RegisterTable(Table):
    table_type: str = 'register'


class ModifyHistory(BaseModel):
    modify_type: str
    description: str


class AssignTable(Table):
    table_type: str = 'assign'
    shifts: list[ShiftForAssign] = []
    employee_usernames: list[str] = []
    modify_history: list[ModifyHistory] = []
