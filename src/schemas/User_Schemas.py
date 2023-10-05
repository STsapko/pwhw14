from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    class Config:
        orm_mode = True


class UserDBScheme(BaseModel):
    username: str
    email: EmailStr
    avatar: str

    class Config:
        orm_mode = True


class UserCreationResponse(BaseModel):
    username: str
    email: EmailStr
    created_at: datetime
    avatar: Optional[str]
    message: Optional[str] = "Created successfully"

    class Config:
        orm_mode = True


class OnLoginResponse(BaseModel):
    user: UserDBScheme
    access_token: str
    refresh_token: str


class RequestEmail(BaseModel):
    email: EmailStr


class RequestDropPassword(BaseModel):
    new_password: str
