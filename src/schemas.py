from datetime import datetime
from src.database.models import LessonDataType
from pydantic import BaseModel

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

class LessonListFullDTO(LessonListReadDTO):
    user_id: int
    username: str | None
    email: str | None

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