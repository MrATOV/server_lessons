from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, LargeBinary, Enum as SQLAlchemyEnum, String, PrimaryKeyConstraint, CheckConstraint
from typing import Annotated, Optional
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

    lessons = relationship("LessonList", secondary="user_lesson", back_populates="users")

class LessonList(Base):
    __tablename__ = 'lesson_list'

    id: Mapped[int_pk]
    title: Mapped[str_nn]
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    private_access: Mapped[bool] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now(), onupdate=datetime.now())
    user_id: Mapped[int] = mapped_column(ForeignKey("user_list.id", ondelete='CASCADE'))
    
    users = relationship("UserList", secondary="user_lesson", back_populates="lessons")

class LessonData(Base):
    __tablename__ = 'lesson_data'

    id: Mapped[int_pk]
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lesson_list.id", ondelete='CASCADE'))
    type: Mapped[LessonDataType] = mapped_column(SQLAlchemyEnum(LessonDataType))
    content: Mapped[str_nn]
    order: Mapped[int] = mapped_column(nullable=False)

class UserLesson(Base):
    __tablename__ = 'user_lesson'
    user_id: Mapped[int] = mapped_column(ForeignKey("user_list.id", ondelete='CASCADE'))
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lesson_list.id", ondelete='CASCADE'))

    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'lesson_id'),
    )

class SourceCode(Base):
    __tablename__ = 'source_code'

    id: Mapped[int_pk]
    path: Mapped[str_nn]
    user_id: Mapped[int] = mapped_column(ForeignKey("user_list.id", ondelete='CASCADE'))

class Notifications(Base):
    __tablename__ = 'notifications'

    id: Mapped[int_pk]
    text: Mapped[str_nn]
    is_read: Mapped[bool] = mapped_column(default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_list.id", ondelete='CASCADE'))

class DefaultData(Base):
    __tablename__ = 'default_data'

    id: Mapped[int_pk]
    type: Mapped[TestDataType] = mapped_column(SQLAlchemyEnum(TestDataType))
    path: Mapped[str_nn]
    user_id: Mapped[int] = mapped_column(ForeignKey("user_list.id", ondelete='CASCADE'))

class TestList(Base):
    __tablename__ = 'test_list'

    id: Mapped[int_pk]
    title: Mapped[str_nn]
    storage_key: Mapped[str_nn]
    date: Mapped[datetime] = mapped_column(default=datetime.now())
    user_id: Mapped[int] = mapped_column(ForeignKey("user_list.id", ondelete='CASCADE'))
    
    data_items = relationship("DataList", back_populates="test", cascade="all, delete")

class ArgumentsList(Base):
    __tablename__ = 'arguments_list'

    id: Mapped[int_pk]
    title: Mapped[str_nn]
    test_id: Mapped[int] = mapped_column(ForeignKey("test_list.id", ondelete='CASCADE'))

    data_associations = relationship("DataArguments", back_populates="arguments", cascade="all, delete")

class DataList(Base):
    __tablename__ = 'data_list'

    id: Mapped[int_pk]
    title: Mapped[str_nn]
    test_id: Mapped[int] = mapped_column(ForeignKey("test_list.id", ondelete='CASCADE'))
    default_data_id: Mapped[Optional[int]] = mapped_column(ForeignKey("default_data.id"), nullable=True)

    test = relationship("TestList", back_populates="data_items")
    arguments = relationship("DataArguments", back_populates="data", cascade="all, delete")
    default_data = relationship("DefaultData")


class DataArguments(Base):
    __tablename__ = 'data_arguments'

    id: Mapped[int_pk]
    args_id: Mapped[int] = mapped_column(ForeignKey("arguments_list.id", ondelete='CASCADE'))
    data_id: Mapped[int] = mapped_column(ForeignKey("data_list.id", ondelete='CASCADE'))

    processing_data: Mapped["ProcessingData | None"] = relationship(back_populates="data_arguments")
    arguments = relationship("ArgumentsList", back_populates="data_associations")
    data = relationship("DataList", back_populates="arguments")
    performance_values = relationship("PerformanceValues", back_populates="data_argument", cascade="all, delete")

class PerformanceValues(Base):
    __tablename__ = 'performance_values'

    id: Mapped[int_pk]
    thread: Mapped[int] = mapped_column()
    time: Mapped[float] = mapped_column()
    acceleration: Mapped[float] = mapped_column()
    efficiency: Mapped[float] = mapped_column()
    cost: Mapped[float] = mapped_column()
    data_arguments_id: Mapped[int] = mapped_column(ForeignKey("data_arguments.id", ondelete='CASCADE'))

    processing_data: Mapped["ProcessingData | None"] = relationship(back_populates="performance_values")
    data_argument = relationship("DataArguments", back_populates="performance_values")

class ProcessingData(Base):
    __tablename__ = 'processing_data'

    id: Mapped[int_pk]
    type: Mapped[TestDataType] = mapped_column(SQLAlchemyEnum(TestDataType))
    path: Mapped[str_nn]
    
    data_arguments_id: Mapped[int | None] = mapped_column(
        ForeignKey("data_arguments.id", ondelete="CASCADE"),
        nullable=True
    )
    data_arguments: Mapped["DataArguments | None"] = relationship(back_populates="processing_data")

    performance_values_id: Mapped[int | None] = mapped_column(
        ForeignKey("performance_values.id", ondelete="CASCADE"),
        nullable=True
    )
    performance_values: Mapped["PerformanceValues | None"] = relationship(back_populates="processing_data")

    __table_args__ = (
        CheckConstraint(
            "(data_arguments_id IS NOT NULL AND performance_values_id IS NULL) OR"
            "(data_arguments_id IS NULL AND performance_values_id IS NOT NULL)",
            name="check_comment_reference"
        ),
    )