from fastapi import HTTPException
from sqlalchemy import select, delete, insert, and_
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from collections import defaultdict

from src.database.core import session
from src.database.models import *
from src.schemas import *
#from src.filesystem import Filesystem


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

async def select_user_email(user_id: int):
    async with session() as s:
        query = select(UserList.email).filter(UserList.id == user_id)
        result = await s.execute(query)
        email = result.scalars().first()
        return email

async def select_user_emails(user_indices: list[int]):
    async with session() as s:
        query = select(UserList.email).filter(UserList.id.in_(user_indices))
        result = await s.execute(query)
        email = result.scalars().all()
        return email

async def select_students():
    async with session() as s:
        query = select(UserList).filter(UserList.role == UserRole.STUDENT)
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
    
async def select_lesson_list_own(user_id):
    async with session() as s:
        query = select(LessonList).filter(LessonList.user_id == user_id)
        result = await s.execute(query)
        lessons = result.scalars().all()
        lessons_dto = [LessonListReadDTO.model_validate(lesson) for lesson in lessons]
        return lessons_dto
    
async def add_user_lessons(user_id):
    async with session() as s:
        query = select(UserList).filter(UserList.id == user_id).options(joinedload(UserList.lessons))
        result = await s.execute(query)
        user = result.scalars().first()
        lessons_dto = [LessonListReadDTO.model_validate(lesson) for lesson in user.lessons]        
        return lessons_dto
    
async def select_lesson_list_public():
    async with session() as s:
        query = select(LessonList).filter(LessonList.private_access == False)
        result = await s.execute(query)
        lessons = result.scalars().all()
        lessons_dto = [LessonListReadDTO.model_validate(lesson) for lesson in lessons]
        return lessons_dto
    
async def select_lesson_title(index: int):
    async with session() as s:
        result = await s.execute(select(LessonList.title).filter(LessonList.id == index))
        title = result.scalars().first()
        return title
        

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
    print(lesson_id)
    print(user_id)
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

async def add_default_data(file_path: str, type: TestDataType, user_id: int):
    try:
        async with session() as s:

            data = DefaultData(type=type, path=file_path, user_id=user_id)
            s.add(data)
            await s.commit()
            return {'message': 'Default data inserting successfully'}
    except IntegrityError:
        await s.rollback()
        raise HTTPException(status_code=500, detail='Default data already exists')
    except:
        await s.rollback()
        raise HTTPException(status_code=500, detail='Error inserting default data')

async def select_default_data(user_id: int):
    async with session() as s:
        query = select(DefaultData).filter(DefaultData.user_id == user_id)
        result = await s.execute(query)
        datas = result.scalars().all()
        data_dto = [DefaultDataDTO.model_validate(data) for data in datas]
        return data_dto

async def select_default_data_type(type: str, user_id: int):
    async with session() as s:
        query = select(DefaultData).filter(DefaultData.user_id == user_id, DefaultData.type == type)
        result = await s.execute(query)
        datas = result.scalars().all()
        data_dto = [DefaultDataDTO.model_validate(data) for data in datas]
        return data_dto
    
async def delete_default_data(data_index: int):
    try:
        async with session() as s:
            result = await s.execute(select(DefaultData).filter(DefaultData.id == data_index))
            lesson_data = result.scalars().first()
            if lesson_data is None:
                raise HTTPException(status_code=404, detail="Lesson data not found")
            result = {
                'message': 'Lesson data deleting successfully',
                'delete_file': lesson_data.path
            }   

            query = delete(DefaultData).filter(DefaultData.id == data_index)
            await s.execute(query)
            await s.commit()
            return result
    except:
        s.rollback()
        raise HTTPException(status_code=500, detail='Error deleting lesson data')
    
async def add_test(test, user_id: int = 1):
    try:
        async with session() as s:
            formatted_str = test["dir"].replace("_", "-", 5).replace("_", ".", 1)
            print(formatted_str)
            dt = datetime.strptime(formatted_str.split('.')[0], "%Y-%m-%d-%H-%M-%S")
            
            test_list_data = TestList(title=test['title'], storage_key=test["dir"], date=dt, user_id=user_id)
            s.add(test_list_data)
            await s.flush()

            all_args = set()
            for data in test["data"]:
                for args_data in data["data"]:
                    all_args.add((args_data["args"]))

            args_indices = []
            for title in all_args:
                args_data = ArgumentsList(title=title, test_id=test_list_data.id)
                s.add(args_data)
                await s.flush()
                args_indices.append(args_data.id)
            
            for data in test["data"]:
                data_list = DataList(title=data["title"], test_id=test_list_data.id)
                s.add(data_list)
                await s.flush()
                for args_id, args_data in zip(args_indices, data["data"]):
                    data_arguments = DataArguments(args_id=args_id, data_id=data_list.id)
                    s.add(data_arguments)
                    await s.flush()

                    if "processing_data" in args_data:
                        proc_data = args_data["processing_data"]
                        if proc_data:
                            processing_data = ProcessingData(
                                type=data["type"],
                                path=proc_data,
                                data_arguments_id=data_arguments.id
                            )
                            s.add(processing_data)
                            await s.flush()

                    for performance in args_data["performance"]:
                        performance_values = PerformanceValues(
                            thread=performance["thread"],
                            time=performance["time"],
                            acceleration=performance["acceleration"],
                            efficiency=performance["efficiency"],
                            cost=performance["cost"],
                            data_arguments_id=data_arguments.id
                        )
                        s.add(performance_values)
                        await s.flush()

                        if "processing_data" in performance:
                            perf_proc_data = performance["processing_data"]
                            if perf_proc_data:
                                processing_data = ProcessingData(
                                type=data["type"],
                                path=perf_proc_data,
                                performance_values_id=performance_values.id
                            )
                        s.add(processing_data)
                        await s.flush()
            
            await s.commit()
            
    except Exception as e:
        await s.rollback()
        raise HTTPException(500, f'Error inserting test {e}')
    
async def get_test_data(test_id: int):
    try:
        async with session() as s: 
            test_query = select(TestList).where(TestList.id == test_id)
            test_result = await s.execute(test_query)
            test = test_result.scalar_one()

            data_query = (
                select(DataList)
                .where(DataList.test_id == test_id)
                .options(
                    joinedload(DataList.default_data),
                    joinedload(DataList.arguments)
                        .joinedload(DataArguments.arguments),
                    joinedload(DataList.arguments)
                        .joinedload(DataArguments.performance_values),
                    joinedload(DataList.arguments)
                        .joinedload(DataArguments.processing_data),
                    joinedload(DataList.arguments)
                        .joinedload(DataArguments.performance_values)
                        .joinedload(PerformanceValues.processing_data)
                )
            )
            data_result = await s.execute(data_query)
            data_items = data_result.scalars().unique().all()

            result = {
                "title": test.title,
                "dir": test.storage_key,
                "data": []
            }

            for data_item in data_items:
                data_entry = {
                    "title": data_item.title,
                    "data": []
                }

                args_performance_map = defaultdict(list)

                for data_arg in data_item.arguments:
                    arg_title = data_arg.arguments.title

                    da_processing_data = None
                    type_processing_data = None
                    if data_arg.processing_data:
                        da_processing_data = data_arg.processing_data.path
                        type_processing_data = data_arg.processing_data.type

                    for perf in data_arg.performance_values:

                        pv_processing_data = None
                        if perf.processing_data:
                            type_processing_data = perf.processing_data.type
                            pv_processing_data = perf.processing_data.path

                        args_performance_map[arg_title].append({
                            "thread": perf.thread,
                            "time": perf.time,
                            "acceleration": perf.acceleration,
                            "efficiency": perf.efficiency,
                            "cost": perf.cost,
                            "processing_data": pv_processing_data
                        })

                for arg_title, performance_list in args_performance_map.items():
                    performance_list.sort(key=lambda x: x["thread"])
                    data_entry["type"] = type_processing_data
                    data_entry["data"].append({
                        "args": arg_title,
                        "processing_data": da_processing_data, 
                        "performance": performance_list
                    })

                data_entry["data"].sort(key=lambda x: x["args"])
                
                result["data"].append(data_entry)

            return result
    except Exception as e:
        await s.rollback()
        raise HTTPException(500, f"Error load test data {e}")
    
async def get_test_list(user_id: int):
    async with session() as s:
        query = select(TestList).filter(TestList.user_id == user_id)
        result = await s.execute(query)
        test_list = result.scalars().all()
        test_list_dto = [TestListReadDTO.model_validate(test) for test in test_list]
        return test_list_dto

async def delete_test_data(id: int):
    try:
        async with session() as s:
            query = delete(TestList).filter(TestList.id == id)
            await s.execute(query)
            await s.commit()
            return {'message': 'Test deleting successfully'}
    except:
        s.rollback()
        raise HTTPException(status_code=500, detail='Error deleting test')
    
async def add_source_code(filepath: str, user_id: int):
    try:
        async with session() as s:

            data = SourceCode(path=filepath, user_id=user_id)
            s.add(data)
            await s.commit()
            return {'message': 'Source code inserting successfully'}
    except IntegrityError:
        await s.rollback()
        raise HTTPException(status_code=500, detail='Source code already exists')
    except:
        await s.rollback()
        raise HTTPException(status_code=500, detail='Error inserting source code')

async def select_source_code_list(user_id: int):
    async with session() as s:
        query = select(SourceCode).filter(SourceCode.user_id == user_id)
        result = await s.execute(query)
        datas = result.scalars().all()
        data_dto = [SourceCodeDTO.model_validate(data) for data in datas]
        return data_dto
    
async def select_source_code(index):
    async with session() as s:
        query = select(SourceCode).filter(SourceCode.id == index)
        result = await s.execute(query)
        data = result.scalars().first()
        data_dto = SourceCodeDTO.model_validate(data)
        return data_dto

async def delete_source_code(index: int):
    try:
        async with session() as s:
            result = await s.execute(select(SourceCode).filter(SourceCode.id == index))
            source_code = result.scalars().first()
            if source_code is None:
                raise HTTPException(status_code=404, detail="Source code not found")
            result = {
                'message': 'Source code deleting successfully',
                'delete_file': source_code.path
            }
                
            query = delete(SourceCode).filter(SourceCode.id == index)
            await s.execute(query)
            await s.commit()
            return result
    except:
        s.rollback()
        raise HTTPException(status_code=500, detail='Error deleting lesson data')
    
async def add_notification(text: str, user_id: int):
    try:
        async with session() as s:
            data = Notifications(text=text, user_id=user_id)
            s.add(data)
            await s.commit()
            return {'message': 'Notification inserting successfully'}
    except:
        await s.rollback()
        raise HTTPException(500, 'Error inserting notification')

async def add_notification_to_users(text: str, user_indices: list[int]):
    try:
        if not user_indices:
            return {"message": "No user indices"}
        
        notifications_data =[{"text": text, "user_id": user_id} for user_id in user_indices]
        
        async with session() as s:
            stmt = insert(Notifications).values(notifications_data)
            
            await s.execute(stmt)
            await s.commit()
            return {'message': 'Notification inserting successfully'}
    except:
        await s.rollback()
        raise HTTPException(500, 'Error inserting notification')
    
async def select_notifications(user_id: int):
    async with session() as s:
        query = select(Notifications).filter(Notifications.user_id == user_id)
        result = await s.execute(query)
        datas = result.scalars().all()
        data_dto = [NotificationsDTO.model_validate(data) for data in datas]
        return data_dto
    
async def read_notification(index: int):
    try:
        async with session() as s:            
            data = await s.get(Notifications, index)
            if not data or data.id != index:
                raise HTTPException(status_code=404, detail="Lesson data not found")
            
            data.is_read = True
            await s.commit()
            await s.refresh(data)
            return {'message': 'Notification read successfully'}
    except:
        s.rollback()
        raise HTTPException(status_code=500, detail='Error read notification')

async def delete_notification(index: int):
    try:
        async with session() as s:
            query = delete(Notifications).filter(Notifications.id == index)
            await s.execute(query)
            await s.commit()
            return {'message': 'Notification deleting successfully'}
    except:
        s.rollback()
        raise HTTPException(500, 'Error deleting notification')