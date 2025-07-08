from fastapi import HTTPException
from sqlalchemy import select, delete, insert, and_, func, over, inspect, text, create_engine
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from collections import defaultdict
from typing import Optional
import os

from src.database.core import session, settings, create_async_engine
from src.database.models import *
from src.schemas import *

from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext

async def insert_lesson(lessonDTO: LessonListDTO, user_id):
    try:
        async with session() as s:
            lesson = LessonList(**lessonDTO.model_dump(), user_id=user_id)
            s.add(lesson)
            await s.commit()
            return {'message': 'Lesson inserting successfully'}
    except IntegrityError:
        await s.rollback()
        raise HTTPException(status_code=500, detail='Lesson already exists')
    except:
        await s.rollback()
        raise HTTPException(status_code=500, detail='Error inserting lesson')
    
async def select_lesson_list_own(user_id, title, total_count, page, page_size):
    async with session() as s:
        filters = [LessonList.user_id == user_id]
        if title:
            filters.append(LessonList.title.ilike(f"%{title}%"))
        query = select(LessonList).filter(and_(*filters)).offset((page - 1) * page_size).limit(page_size)
        result = await s.execute(query)
        lessons = result.scalars().all()
        lessons_dto = [LessonListReadDTO.model_validate(lesson) for lesson in lessons]

        if not total_count:
            count_query = (
                select(func.count())
                .select_from(LessonList)
                .filter(and_(*filters))
            )
            count_result = await s.execute(count_query)
            total_count = count_result.scalar()
        return {
            'data': lessons_dto,
            'total_count': total_count
        }

async def select_lesson_list_admin(
    title: str | None,
    username: str | None,
    email: str | None,
    total_count: int | None,
    page: int,
    page_size: int
):
    async with session() as s:
        filters = []
        user_filters = []
        
        if title:
            filters.append(LessonList.title.ilike(f"%{title}%"))
        
        if username:
            user_filters.append(UserList.username.ilike(f"%{username}%"))
        if email:
            user_filters.append(UserList.email.ilike(f"%{email}%"))
        
        base_query = (
            select(
                LessonList,
                UserList.username,
                UserList.email
            )
            .join(UserList, LessonList.user_id == UserList.id)
        )
        
        if filters:
            base_query = base_query.filter(and_(*filters))
        if user_filters:
            base_query = base_query.filter(and_(*user_filters))
        
        query = base_query.offset((page - 1) * page_size).limit(page_size)
        
        result = await s.execute(query)
        
        lessons_dto = []
        for lesson, username, email in result:
            lesson_data = {
                **lesson.__dict__,
                "username": username,
                "email": email
            }
            lesson_data.pop("_sa_instance_state", None)
            lessons_dto.append(LessonListFullDTO.model_validate(lesson_data))

        if not total_count:
            count_query = select(func.count()).select_from(LessonList).join(UserList)
            
            if filters:
                count_query = count_query.filter(and_(*filters))
            if user_filters:
                count_query = count_query.filter(and_(*user_filters))
            
            count_result = await s.execute(count_query)
            total_count = count_result.scalar()
            
        return {
            'data': lessons_dto,
            'total_count': total_count
        }
    
async def select_user_lessons(user_id, title, total_count, page, page_size):
    async with session() as s:
        filters = [UserLesson.user_id == user_id]
        if title:
            filters.append(LessonList.title.ilike(f"%{title}%"))
        
        query = (
            select(LessonList)
            .join(UserLesson, LessonList.id == UserLesson.lesson_id)
            .filter(and_(*filters))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        
        result = await s.execute(query)
        lessons = result.scalars().all()
        lessons_dto = [LessonListReadDTO.model_validate(lesson) for lesson in lessons]

        if not total_count:
            count_query = (
                select(func.count())
                .select_from(LessonList)
                .join(UserLesson, LessonList.id == UserLesson.lesson_id)
                .filter(and_(*filters))
            )
            count_result = await s.execute(count_query)
            total_count = count_result.scalar()
            
        return {
            'data': lessons_dto,
            'total_count': total_count
        }
    
async def select_lesson_list_public(title, total_count, page, page_size):
    async with session() as s:
        filters = [LessonList.private_access == False]
        if title:
            filters.append(LessonList.title.ilike(f"%{title}%"))
        query = select(LessonList).filter(and_(*filters)).offset((page - 1) * page_size).limit(page_size)
        result = await s.execute(query)
        lessons = result.scalars().all()
        lessons_dto = [LessonListReadDTO.model_validate(lesson) for lesson in lessons]
        
        if not total_count:
            count_query = (
                select(func.count())
                .select_from(LessonList)
                .filter(and_(*filters))
            )
            count_result = await s.execute(count_query)
            total_count = count_result.scalar()
        return {
            'data': lessons_dto,
            'total_count': total_count
        }
        

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
    
async def subscribe_lesson(lesson_id: int, user_id: int):
    try:
        async with session() as s:
            data = UserLesson(user_id=user_id, lesson_id=lesson_id)
            s.add(data)
            await s.commit()
            return {'message': 'Lesson user inserting successfully'}
    except IntegrityError:
        await s.rollback()
        raise HTTPException(status_code=500, detail="Lesson user already exists")
    except:
        await s.rollback()
        raise HTTPException(status_code=500, detail="Error inserting lesson user")

async def unsubscribe_lesson(lesson_id: int, user_id: int):
    try:
        async with session() as s:
            query = delete(UserLesson).filter(and_(UserLesson.lesson_id == lesson_id, UserLesson.user_id == user_id))
            await s.execute(query)
            await s.commit()
            return {'message': 'Lesson user deleting successfully'}
    except:
        await s.rollback()
        raise HTTPException(status_code=500, detail="Error inserting lesson user")

async def select_lesson_headers(lesson_id: int, page_size: int = 100):
    async with session() as s:
        subq = (
            select(
                LessonData.id,
                LessonData.type,
                LessonData.content,
                LessonData.order,
                func.row_number().over(order_by=LessonData.order).label('row_num')
            )
            .where(LessonData.lesson_id == lesson_id)
            .order_by(LessonData.order)
            .subquery()
        )

        stmt = (
            select(
                subq.c.row_num.label('new_index'),
                subq.c.id,
                subq.c.type,
                subq.c.content,
                subq.c.order
            )
            .where(subq.c.type == 'header')
            .order_by(subq.c.row_num)
        )
        result = await s.execute(stmt)

        headers = [{
            "id": row.new_index,
            "real_id": row.id,
            "content": row.content,
            "order": row.order,
            "page": ((row.new_index - 1) // page_size) + 1
        } for row in result]
        return headers


async def select_lesson_data(lesson_id: int, total_count: Optional[int] = None, page: int = 1, page_size: int = 100, is_editing: bool = False):
    async with session() as s:

        query = select(LessonData).filter(LessonData.lesson_id == lesson_id).offset((page - 1) * page_size).limit(page_size).order_by(LessonData.order)
        result = await s.execute(query)
        lessons = result.scalars().all()
        lessons_dto = [LessonDataReadDTO.model_validate(lesson) for lesson in lessons]

        if not total_count:
            count_query = (
                select(func.count())
                .filter(and_(LessonData.lesson_id == lesson_id))
            )
            count_result = await s.execute(count_query)
            total_count = count_result.scalar()

        prev_item = None
        if is_editing and page > 1:
            prev_query = (
                select(LessonData)
                .filter(LessonData.lesson_id == lesson_id)
                .offset((page - 2) * page_size + (page_size - 1))
                .limit(1)
                .order_by(LessonData.order)
            )
            prev_result = await s.execute(prev_query)
            prev_item_obj = prev_result.scalars().first()
            if prev_item_obj:
                prev_item = LessonDataReadDTO.model_validate(prev_item_obj)

        next_item = None
        if is_editing and page * page_size < total_count:
            next_query = (
                select(LessonData)
                .filter(LessonData.lesson_id == lesson_id)
                .offset(page * page_size)
                .limit(1)
                .order_by(LessonData.order)
            )
            next_result = await s.execute(next_query)
            next_item_obj = next_result.scalars().first()
            if next_item_obj:
                next_item = LessonDataReadDTO.model_validate(next_item_obj)

        headers = await select_lesson_headers(lesson_id, page_size)
        teacher_query = select(LessonList).filter(LessonList.id == lesson_id)
        teacher_result = await s.execute(teacher_query)
        teacher = teacher_result.scalars().first()

        return {
            'data': lessons_dto,
            'total_count': total_count,
            'headers': headers,
            'teacher_id': teacher.user_id,
            'boundary': {
                'prev': prev_item,
                'next': next_item
            }
        } 
        
    
async def delete_lesson_data(data_index: int):
    try:
        async with session() as s:
            result = await s.execute(select(LessonData).filter(LessonData.id == data_index))
            lesson_data = result.scalars().first()
            if lesson_data is None:
                raise HTTPException(status_code=404, detail="Lesson data not found")
            result = {'message': 'Lesson data deleting successfully'}
            if (lesson_data.type in (LessonDataType.IMAGE, LessonDataType.AUDIO, LessonDataType.VIDEO) and not lesson_data.content.startswith("http")):
                result['delete_file'] = lesson_data.content
                

            query = delete(LessonData).filter(LessonData.id == data_index)
            await s.execute(query)
            await s.commit()
            return result
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
                result["delete_file"] = data.content
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