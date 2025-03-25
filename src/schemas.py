from datetime import datetime
from src.database.models import LessonDataType, UserRole
from pydantic import BaseModel, field_validator
import hashlib


class UserListDTO(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole
    
    @field_validator('password', mode="before")
    def set_password(cls, v):
        hash_object = hashlib.sha3_256(v.encode())
        return hash_object.hexdigest()


class UserListReadDTO(BaseModel):
    id: int
    username: str
    email: str
    password: str
    role: UserRole

    def compare_password(self, password: str):
        hash_object = hashlib.sha3_256(password.encode())
        hash_password = hash_object.hexdigest()
        return self.password == hash_password
    
    class Config:
        from_attributes = True

class LessonListDTO(BaseModel):
    title: str

class LessonListReadDTO(LessonListDTO):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LessonDataDTO(BaseModel):

    type: LessonDataType
    content: str
    order: int

class LessonDataUpdateDTO(LessonDataDTO):
    id: int

class LessonDataReadDTO(LessonDataUpdateDTO):
    lesson_id: int

    class Config:
        from_attributes = True