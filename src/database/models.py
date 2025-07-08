from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Enum as SQLAlchemyEnum, String, PrimaryKeyConstraint
from typing import Annotated
from datetime import datetime
from enum import Enum

class Base(DeclarativeBase): pass

int_pk = Annotated[int, mapped_column(primary_key=True, index=True)]
str_nn = Annotated[str, mapped_column(nullable=False)]

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
    NOTCONFIRMED = 'not_confirmed'

class UserList(Base):
    __tablename__ = 'users'
    id: Mapped[int_pk]
    username: Mapped[str_nn]
    email: Mapped[str_nn]
    password: Mapped[str_nn]
    avatar: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[UserRole] = mapped_column(SQLAlchemyEnum(UserRole))

    lessons = relationship("LessonList", secondary="user_lesson", back_populates="users")

class UserGroup(Base):
    __tablename__ = 'user_group'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id', ondelete='CASCADE'))

    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'group_id'),
    )

class LessonList(Base):
    __tablename__ = 'lessons'

    id: Mapped[int_pk]
    title: Mapped[str_nn]
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    private_access: Mapped[bool] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now(), onupdate=datetime.now())
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete='CASCADE'))
    
    users = relationship("UserList", secondary="user_lesson", back_populates="lessons")

class LessonData(Base):
    __tablename__ = 'lesson_data'

    id: Mapped[int_pk]
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete='CASCADE'))
    type: Mapped[LessonDataType] = mapped_column(SQLAlchemyEnum(LessonDataType))
    content: Mapped[str_nn]
    order: Mapped[int] = mapped_column(nullable=False)

class UserLesson(Base):
    __tablename__ = 'user_lesson'
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete='CASCADE'))
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete='CASCADE'))

    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'lesson_id'),
    )