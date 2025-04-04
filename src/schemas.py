from datetime import datetime
from src.database.models import LessonDataType, UserRole, TestDataType
from src.data_generator import DataType, FillType
from pydantic import BaseModel, field_validator, EmailStr
import hashlib
from typing import Optional, Union

class GenerateDataTypeDTO(BaseModel):
    dataType: DataType
    filename: str

class RandomDTO(GenerateDataTypeDTO):
    min: Union[int, float]
    max: Union[int, float]

class OrderDTO(GenerateDataTypeDTO):
    fillType: FillType
    start: Union[int, float]
    step: Union[int, float]
    interval: int

class RandomArrayDTO(RandomDTO):
    size: int

class OrderArrayDTO(OrderDTO):
    size: int

class RandomMatrixDTO(RandomDTO):
    rows: int
    cols: int

class OrderMatrixDTO(OrderDTO):
    rows: int
    cols: int
    
class TextDTO(BaseModel):
    text: str
    filename: str

class UserListDTO(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole
    
    @field_validator('password', mode="before")
    def set_password(cls, v):
        hash_object = hashlib.sha3_256(v.encode())
        return hash_object.hexdigest()


class TestListReadDTO(BaseModel):
    id: int
    title: str
    storage_key: str
    date: datetime

    class Config:
        from_attributes = True

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
    private_access: bool
    description: str

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

class DefaultDataDTO(BaseModel):
    id: int
    type: TestDataType
    path: str
    user_id: int

    class Config:
        from_attributes = True

class SourceCodeDTO(BaseModel):
    id: int
    path: str
    user_id: int

    class Config:
        from_attributes = True

class NotificationDTO(BaseModel):
    user_id: int
    text: str

class NotificationWriteDTO(NotificationDTO):
    task_id: str

class NotificationsDTO(NotificationDTO):
    id: int
    is_read: bool

    class Config:
        from_attributes = True

class EmailSchema(BaseModel):
    email_to: EmailStr
    subject: str
    body: str

class EmailWithAttachmentSchema(EmailSchema):
    attachement: bytes
    filename: str

class BroadcastDTO(BaseModel):
    token: str
    user_indices: list[int]
    lesson_id: int