from datetime import datetime
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    user_id: str
    role: str
    username: str
    password: str
    first_name: str
    last_name: str
    address: str
    email: EmailStr
    phone_number: str
    gender: str | None = None


class ShiftForEmployee(BaseModel):
    shift_name: str
    date: datetime
    username: str | None = None


class Employee(User):
    role: str = 'Employee'
    worked_shifts: list[ShiftForEmployee] = []
    manager_username: str


class Manager(User):
    role: str = 'Manager'


class ClientUser(BaseModel):
    user_id: str
    role: str
    username: str
    first_name: str
    last_name: str
    address: str
    email: EmailStr
    phone_number: str
    gender: str | None = None
    worked_shifts: list[ShiftForEmployee] | None = None
    manager_username: str | None = None
