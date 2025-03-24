from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from src.database.core import session
from src.database.models import *
from src.schemas import *
from src.filesystem import Filesystem


async def insert_user(userDTO: UserListDTO):
    try:
        async with session() as s:
            user = UserList(**userDTO.model_dump())
            s.add(user)
            await s.commit()
            return {'message': 'User inserting successfully'}
    except:
        raise HTTPException(status_code=500, detail='Error inserting user')
    
async def select_users():
    async with session() as s:
        query = select(UserList)
        result = await s.execute(query)
        users = result.scalars().all()
        users_dto = [UserListReadDTO.model_validate(user) for user in users]
        return users_dto
    
async def select_user(email: str):
    async with session() as s:
        query = select(UserList).filter(UserList.email == email)
        result = await s.execute(query)
        user = result.scalar()
        user_dto = UserListReadDTO.model_validate(user)
        return user_dto
    
async def delete_user(index: int):
    try:
        async with session() as s:
            query = delete(UserList).filter(UserList.id == index)
            await s.execute(query)
            await s.commit()
            return {'message': 'User deleting successfully'}
    except:
        raise HTTPException(status_code=500, detail='Error deleting user')

async def insert_lesson(lessonDTO: LessonListDTO):
    try:
        async with session() as s:
            lesson = LessonList(**lessonDTO.model_dump())
            s.add(lesson)
            await s.commit()
            return {'message': 'Lesson inserting successfully'}
    except IntegrityError:
        await s.rollback()
        raise HTTPException(status_code=500, detail='Lesson already exists')
    except:
        await s.rollback()
        raise HTTPException(status_code=500, detail='Error inserting lesson')
    
async def select_lesson_list():
    async with session() as s:
        query = select(LessonList)
        result = await s.execute(query)
        lessons = result.scalars().all()
        lessons_dto = [LessonListReadDTO.model_validate(lesson) for lesson in lessons]
        return lessons_dto
    
async def delete_lesson(index: int):
    try:
        async with session() as s:
            query = delete(LessonList).filter(LessonList.id == index)
            await s.execute(query)
            await s.commit()
            return {'message': 'Lesson deleting successfully'}
    except:
        s.rollback()
        raise HTTPException(status_code=500, detail='Error deleting lesson')

async def add_lesson_data(lesson_data: LessonDataDTO, lesson_id: int):
    try:
        async with session() as s:

            data = LessonData(**lesson_data.model_dump())
            data.lesson_id = lesson_id
            s.add(data)
            await s.commit()
            return {'message': 'Lesson data inserting successfully'}
    except IntegrityError:
        await s.rollback()
        raise HTTPException(status_code=500, detail='Lesson data already exists')
    except:
        await s.rollback()
        raise HTTPException(status_code=500, detail='Error inserting lesson data')
    
async def select_lesson_data(lesson_id: int):
    async with session() as s:
        query = select(LessonData).filter(LessonData.lesson_id == lesson_id).order_by(LessonData.order)
        result = await s.execute(query)
        lessons = result.scalars().all()
        lessons_dto = [LessonDataReadDTO.model_validate(lesson) for lesson in lessons]
        return lessons_dto
    
async def delete_lesson_data(data_index: int):
    try:
        async with session() as s:
            result = await s.execute(select(LessonData).filter(LessonData.id == data_index))
            lesson_data = result.scalars().first()
            if lesson_data is None:
                raise HTTPException(status_code=404, detail="Lesson data not found")
            if (lesson_data.type == 'image' and not lesson_data.content.startswith("http")):
                filename = lesson_data.content
                fs = Filesystem()
                fs.delete_image(filename)

            query = delete(LessonData).filter(LessonData.id == data_index)
            await s.execute(query)
            await s.commit()
            return {'message': 'Lesson data deleting successfully'}
    except:
        s.rollback()
        raise HTTPException(status_code=500, detail='Error deleting lesson data')
    
async def update_lesson_data(lesson_data: LessonDataUpdateDTO, lesson_id: int, index: int):
    try:
        async with session() as s:            
            data = await s.get(LessonData, index)
            if not data or data.lesson_id != lesson_id:
                raise HTTPException(status_code=404, detail="Lesson data not found")
            
            result = {'message': 'Lesson data updating successfully'}
            if data.type == 'image' and not lesson_data.content.startswith("http") and data.content != lesson_data.content:
                filename = data.content
                fs = Filesystem()
                fs.delete_image(filename)
                result["filename"] = lesson_data.content
            
            data.order = lesson_data.order
            data.content = lesson_data.content
            data.type = lesson_data.type

            await s.commit()

            await s.refresh(data)

            return result
    except:
        s.rollback()
        raise HTTPException(status_code=500, detail='Error updating lesson data')