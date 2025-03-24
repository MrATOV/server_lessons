from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, LargeBinary, Enum as SQLAlchemyEnum
from typing import Annotated
from datetime import datetime, timezone
from enum import Enum

class Base(DeclarativeBase): pass

int_pk = Annotated[int, mapped_column(primary_key=True, index=True)]
str_nn = Annotated[str, mapped_column(nullable=False)]

class TestDataType(str, Enum):
    ARRAY = 'array'
    MATRIX = 'matrix'
    TEXT = 'text'
    IMAGE = 'image'
    AUDIO = 'audio'
    VIDEO = 'video'

class LessonDataType(str, Enum):
    TEXT = 'text'
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'
    HEADER = 'header'
    CODE = 'code'

class UserRole(str, Enum):
    STUDENT = 'student'
    TEACHER = 'teacher'
    ADMIN = 'admin'

class UserList(Base):
    __tablename__ = 'user_list'
    id: Mapped[int_pk]
    username: Mapped[str_nn]
    email: Mapped[str_nn]
    password: Mapped[str_nn]
    role: Mapped[UserRole] = mapped_column(SQLAlchemyEnum(UserRole))

class LessonList(Base):
    __tablename__ = 'lesson_list'

    id: Mapped[int_pk]
    title: Mapped[str_nn]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now(), onupdate=datetime.now())
    
class LessonData(Base):
    __tablename__ = 'lesson_data'

    id: Mapped[int_pk]
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lesson_list.id", ondelete='CASCADE'))
    type: Mapped[LessonDataType] = mapped_column(SQLAlchemyEnum(LessonDataType))
    content: Mapped[str_nn]
    order: Mapped[int] = mapped_column(nullable=False)

class UserLesson(Base):
    __tablename__ = 'user_lesson'
    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(ForeignKey("user_list.id", ondelete='CASCADE'))
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lesson_list.id", ondelete='CASCADE'))

class DefaultData(Base):
    __tablename__ = 'default_data'

    id: Mapped[int_pk]
    type: Mapped[TestDataType] = mapped_column(SQLAlchemyEnum(TestDataType))
    path: Mapped[str_nn]

class ProcessingData(Base):
    __tablename__ = 'processing_data'

    id: Mapped[int_pk]
    type: Mapped[TestDataType] = mapped_column(SQLAlchemyEnum(TestDataType))
    path: Mapped[str_nn]

class ResearchList(Base):
    __tablename__ = 'research_list'

    id: Mapped[int_pk]
    title: Mapped[str_nn]
    date: Mapped[datetime] = mapped_column(default=datetime.now())
    user_id: Mapped[int] = mapped_column(ForeignKey("lesson_list.id", ondelete='CASCADE'))

class Parameters(Base):
    __tablename__ = 'parameters'

    id: Mapped[int_pk]
    title: Mapped[str_nn]
    research_id: Mapped[int] = mapped_column(ForeignKey("research_list.id"))

class DataParameters(Base):
    __tablename__ = 'data_parameters'

    id: Mapped[int_pk]
    data_id: Mapped[int] = mapped_column(ForeignKey("default_data.id"))
    parameters_id: Mapped[int] = mapped_column(ForeignKey("parameters.id"))

class PerformanceEvaluation(Base):
    __tablename__ = 'performance_evaluation'

    id: Mapped[int_pk]
    thread: Mapped[int] = mapped_column()
    time: Mapped[float] = mapped_column()
    acceleration: Mapped[float] = mapped_column()
    efficiency: Mapped[float] = mapped_column()
    cost: Mapped[float] = mapped_column()