from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
import json
import uvicorn
from alembic.config import Config
from alembic import command
import mimetypes
import os

from src.schemas import *
import src.database.orm as ORM
from src.filesystem import Filesystem
import src.security as Security
from src.s3_client import S3Client
from src.redis_client import RedisClient
from src.report import generate_performance_report
from src.email_service import EmailService
from src.utils import *

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600
)

s3_client = S3Client()
redis_client = RedisClient()
fs = Filesystem()
email_service = EmailService()

@app.get('/users')
async def get_users():
    users = await ORM.select_users()
    return users

@app.get('/users/students')
async def get_students(current_user: dict = Depends(Security.get_current_user)):
    if current_user.get("role") != 'teacher':
        raise HTTPException(500, 'Not teacher')
    users = await ORM.select_students()
    return users

@app.post('/users/register')
async def register(user: UserListDTO):
    return await ORM.insert_user(user)

@app.post('/users/login')
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await Security.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail='Incorrect username or password')
    access_token = Security.create_access_token(user.model_dump())
    return {'access_token': access_token, 'token_type': 'bearer'}

@app.get('/users/protected')
async def get_user_id(current_user: dict = Depends(Security.get_current_user)):
    return current_user

@app.get('/users/lessons')
async def get_user_lessons(current_user: dict = Depends(Security.get_current_user)):
    return await ORM.add_user_lessons(current_user.get("id"))

@app.delete('/users/{index}')
async def delete_user(index: int):
    return ORM.delete_user(index)

@app.post('/lesson')
async def insert_lesson(lesson: LessonListDTO, current_user: dict = Depends(Security.get_current_user)):
    return await ORM.insert_lesson(lesson, current_user.get("id"))

@app.get("/lesson/list/own")
async def get_lesson_list_own(current_user: dict = Depends(Security.get_current_user)):
    lessons = await ORM.select_lesson_list_own(current_user.get("id"))
    return lessons

@app.get("/lesson/list/public")
async def get_lesson_list_public():
    lessons = await ORM.select_lesson_list_public()
    return lessons

@app.get('/lesson/{index}/token')
async def get_lesson_token(index: int, current_user: dict = Depends(Security.get_current_user)):
    return redis_client.create_token(index)

@app.post("/lesson/{index}/subscribe")
async def subscribe_lesson(index: int, current_user: dict = Depends(Security.get_current_user)):
    return await ORM.subscribe_lesson(index, current_user.get("id"))

@app.post("/lesson/private/subscribe/{token}")
async def subscribe_private_lesson(token: str, current_user: dict = Depends(Security.get_current_user)):
    lesson_id = redis_client.verify_token(token)
    return await ORM.subscribe_lesson(lesson_id, current_user.get("id"))

@app.delete("/lesson/{index}/unsubscribe")
async def unsubscribe_lesson(index: int, current_user: dict = Depends(Security.get_current_user)):
    return await ORM.unsubscribe_lesson(index, current_user.get("id"))

@app.delete("/lesson/{index}")
async def delete_lesson(index: int, current_user: dict = Depends(Security.get_current_user)):
    return await ORM.delete_lesson(index)

@app.post('/lesson/{index}/data')
async def insert_lesson_data(index: int, lesson_data: str = Form(...), file: Optional[UploadFile] = File(None), current_user: dict = Depends(Security.get_current_user)):
    try:
        data_dict = json.loads(lesson_data)
        data = LessonDataDTO(**data_dict)
    except:
        raise HTTPException(status_code=400, detail="Invalid lesson data")
    if data.type in (LessonDataType.IMAGE, LessonDataType.AUDIO, LessonDataType.VIDEO) and data.content == "":
        if not file:
            raise HTTPException(status_code=400, detail="Image file is required")
        data.content = await s3_client.upload_media_file(file, data.type.value, index)
    return await ORM.add_lesson_data(data, index)

@app.get("/lesson/{index}/data")
async def get_lesson_data(index: int):
    return await ORM.select_lesson_data(index)

@app.put("/lesson/{index}/data/{data_index}")
async def update_lesson_data(index: int, data_index: int, lesson_data: str = Form(...), file: Optional[UploadFile] = File(None)):
    try:
        data_dict = json.loads(lesson_data)
        data = LessonDataUpdateDTO(**data_dict)
    except:
        raise HTTPException(status_code=400, detail="Invalid lesson data")
    if data.type in (LessonDataType.IMAGE, LessonDataType.AUDIO, LessonDataType.VIDEO) and data.content == "":
        if not file:
            raise HTTPException(status_code=400, detail="Image file is required")
        data.content = await s3_client.upload_media_file(file, data.type.value, index)

    result = await ORM.update_lesson_data(data, index, data_index)
    if 'delete_file' in result:
        s3_client.delete_file(result['delete_file'], True)
        result.pop('delete_file')
    return result

@app.delete("/lesson/{index}/data/{data_index}")
async def delete_lesson_data(index: int, data_index: int, current_user: dict = Depends(Security.get_current_user)):
    result = await ORM.delete_lesson_data(data_index)
    if 'delete_file' in result:
        s3_client.delete_file(result["delete_file"], True)
    return result["message"]

@app.get('/data/list')
async def get_data_list(current_user: dict = Depends(Security.get_current_user)):
    data = await ORM.select_default_data(current_user.get("id"))
    for item in data:
        item.path = os.path.basename(item.path)
    return data

@app.get('/data/list/{type}')
async def get_data_list_type(type: str, current_user: dict = Depends(Security.get_current_user)):
    data = await ORM.select_default_data_type(type, current_user.get("id"))
    for item in data:
        item.path = os.path.basename(item.path)
    return data

@app.post("/data/array/random")
async def create_random_array(data: RandomArrayDTO, current_user: dict = Depends(Security.get_current_user)):
    filename = fs.create_random_array(data)
    filepath = s3_client.upload_file_from_path(filename, current_user["id"])
    return await ORM.add_default_data(filepath, "array", current_user.get("id"))

@app.post("/data/array/order")
async def create_order_array(data: OrderArrayDTO, current_user: dict = Depends(Security.get_current_user)):
    filename = fs.create_order_array(data)
    filepath = s3_client.upload_file_from_path(filename, current_user["id"])
    return await ORM.add_default_data(filepath, "array", current_user.get("id"))

@app.get("/data/array/{filename}")
async def get_array_data(filename: str, path: str = 'default', offset: int = 1, limit: int = 100, current_user: dict = Depends(Security.get_current_user)):
    if path == 'default':
        temp_file_path = s3_client.get_temporary_file(current_user["id"], 'array', filename)
    else:
        temp_file_path = s3_client.get_temporary_file(current_user["id"], f'proc/{path}', filename)

    return fs.get_array(temp_file_path, offset, limit)

@app.post("/data/matrix/random")
async def create_random_matrix(data: RandomMatrixDTO, current_user: dict = Depends(Security.get_current_user)):
    filename = fs.create_random_matrix(data)
    filepath = s3_client.upload_file_from_path(filename, current_user["id"])
    return await ORM.add_default_data(filepath, "matrix", current_user.get("id"))

@app.post("/data/matrix/order")
async def create_order_matrix(data: OrderMatrixDTO, current_user: dict = Depends(Security.get_current_user)):
    filename = fs.create_order_matrix(data)
    filepath = s3_client.upload_file_from_path(filename, current_user["id"])
    return await ORM.add_default_data(filepath, "matrix", current_user.get("id"))

@app.get("/data/matrix/{filename}")
async def get_matrix_data(filename: str, path: str = "default", page_row: int = 1, limit_row: int = 10, page_col: int = 1, limit_col: int = 10, current_user: dict = Depends(Security.get_current_user)):
    if path == 'default':
        temp_file_path = s3_client.get_temporary_file(current_user["id"], 'matrix', filename)
    else:
        temp_file_path = s3_client.get_temporary_file(current_user["id"], f'proc/{path}', filename)

    return fs.get_matrix(temp_file_path, page_row, limit_row, page_col, limit_col)

@app.post("/data/text/content")
async def create_text_data(data: TextDTO, current_user: dict = Depends(Security.get_current_user)):
    filename = fs.create_text(data)
    filepath = s3_client.upload_file_from_path(filename, current_user["id"])
    return await ORM.add_default_data(filepath, "text", current_user.get("id"))

@app.get("/data/text/{filename}")
async def get_text_data(filename: str, path: str = 'default', current_user: dict = Depends(Security.get_current_user)):
    if path == 'default':
        temp_file_path = s3_client.get_temporary_file(current_user["id"], 'text', filename)
    else:
        temp_file_path = s3_client.get_temporary_file(current_user["id"], f'proc/{path}', filename)

    return fs.get_text_data(temp_file_path)

@app.get("/data/code")
async def get_source_code_list(current_user: dict = Depends(Security.get_current_user)):
    return await ORM.select_source_code_list(current_user.get("id"))

@app.get("/data/code/{index}")
async def get_source_code(index: int, current_user: dict = Depends(Security.get_current_user)):
    data = await ORM.select_source_code(index)
    content = s3_client.get_source_code(data.path)
    return content

@app.post("/data/code")
async def create_source_code(code: TextDTO, current_user: dict = Depends(Security.get_current_user)):
    filepath = s3_client.create_source_code(code.text, code.filename, current_user.get("id")) 
    return await ORM.add_source_code(filepath, current_user.get("id"))

@app.put("/data/code")
async def put_source_code(code: TextDTO, current_user: dict = Depends(Security.get_current_user)):
    s3_client.put_source_code(code.text, code.filename, current_user.get("id")) 

@app.delete("/data/code/{index}")
async def delete_source_code(index: int):
    result = await ORM.delete_source_code(index)
    if "delete_file" in result:
        s3_client.delete_file(result.pop("delete_file"), False)
    return result

@app.post("/data/{type}")
async def create_data(type: str, file: UploadFile = File(...), current_user: dict = Depends(Security.get_current_user)):
    filepath = s3_client.upload_file_private(type, file, current_user["id"])
    return await ORM.add_default_data(filepath, type, current_user.get("id"))

@app.get("/data/image/{filename}")
async def get_data_image(filename: str, background_tasks: BackgroundTasks, path: str = 'default', current_user: dict = Depends(Security.get_current_user)):
    if path == 'default':
        local_file_path = s3_client.get_temporary_file(current_user["id"], 'image', filename)
    else:
        local_file_path = s3_client.get_temporary_file(current_user["id"], f'proc/{path}', filename)

    media_type, _ = mimetypes.guess_type(filename)
    if not media_type:
        media_type = "image/jpeg"
    background_tasks.add_task(delete_file, local_file_path)
    return FileResponse(local_file_path, media_type=media_type)

@app.get("/data/audio/{filename}")
async def get_data_image(filename: str, background_tasks: BackgroundTasks, path: str = 'default', current_user: dict = Depends(Security.get_current_user)):
    if path == 'default':
        local_file_path = s3_client.get_temporary_file(current_user["id"], 'audio', filename)
    else:
        local_file_path = s3_client.get_temporary_file(current_user["id"], f'proc/{path}', filename)
    media_type, _ = mimetypes.guess_type(filename)
    if not media_type:
        media_type = "audio/mp3"
    background_tasks.add_task(delete_file, local_file_path)
    return FileResponse(local_file_path, media_type=media_type)

@app.get("/data/video/{filename}")
async def get_data_image(filename: str, background_tasks: BackgroundTasks, path: str = 'default', current_user: dict = Depends(Security.get_current_user)):
    if path == 'default':
        local_file_path = s3_client.get_temporary_file(current_user["id"], 'video', filename)
    else:
        local_file_path = s3_client.get_temporary_file(current_user["id"], f'proc/{path}', filename)
        
    media_type, _ = mimetypes.guess_type(filename)
    if not media_type:
        media_type = "video/mp4"
    background_tasks.add_task(delete_file, local_file_path)
    return FileResponse(local_file_path, media_type=media_type)

@app.delete("/data/{id}")
async def delete_data(id: int, current_user: dict = Depends(Security.get_current_user)):
    result = await ORM.delete_default_data(id)
    s3_client.delete_file(result["delete_file"], False)

@app.get("/image/{lesson_id}/{filename}")
async def get_image(lesson_id: str, filename: str, background_tasks: BackgroundTasks):
    local_file_path = s3_client.get_file("image", lesson_id, filename)
    media_type, _ = mimetypes.guess_type(filename)
    if not media_type:
        media_type = "image/jpeg"
    background_tasks.add_task(delete_file, local_file_path)
    return FileResponse(local_file_path, media_type=media_type)

@app.get("/audio/{lesson_id}/{filename}")
async def get_audio(lesson_id: str, filename: str, background_tasks: BackgroundTasks):
    local_file_path = s3_client.get_file("audio", lesson_id, filename)
    media_type, _ = mimetypes.guess_type(filename)
    if not media_type:
        media_type = "video/mp4"
    background_tasks.add_task(delete_file, local_file_path)
    return FileResponse(local_file_path, media_type=media_type)

@app.get("/video/{lesson_id}/{filename}")
async def get_video(lesson_id: str, filename: str, background_tasks: BackgroundTasks):
    local_file_path = s3_client.get_file("video", lesson_id, filename)
    media_type, _ = mimetypes.guess_type(filename)
    if not media_type:
        media_type = "audio/mp3"
    background_tasks.add_task(delete_file, local_file_path)
    return FileResponse(local_file_path, media_type=media_type)

@app.post('/report')
async def generate_report(data:dict, background_tasks: BackgroundTasks):
    report_file = generate_performance_report(data)
    background_tasks.add_task(delete_file, report_file)

    return FileResponse(report_file, media_type="application/pdf", filename="report.pdf")

@app.get("/test/list")
async def get_test_list(current_user: dict = Depends(Security.get_current_user)):
    return await ORM.get_test_list(current_user["id"])

@app.post('/test')
async def add_test(data: dict, current_user: dict = Depends(Security.get_current_user)):
    await ORM.add_test(data, current_user["id"])

@app.get("/test/{id}")
async def get_test_data(id: int, current_user: dict = Depends(Security.get_current_user)):
    return await ORM.get_test_data(id)

@app.delete("/test/{id}")
async def delete_test_data(id: int, current_user: dict = Depends(Security.get_current_user)):
    return await ORM.delete_test_data(id)

@app.post("/notifications")
async def create_notification(notification: NotificationWriteDTO):
    email = await ORM.select_user_email(notification.user_id)
    email_data = EmailSchema(email_to=email, subject="Новое уведомление!", body=get_notification_mail(notification.text, notification.task_id))
    await email_service.send_email(email_data)
    return await ORM.add_notification(get_notification_markdown(notification.text, notification.task_id), notification.user_id)

@app.get('/notifications')
async def get_notifications(current_user: dict = Depends(Security.get_current_user)):
    return await ORM.select_notifications(current_user.get("id"))

@app.put('/notifications/{index}')
async def read_notification(index: int, current_user: dict = Depends(Security.get_current_user)):
    return await ORM.read_notification(index)

@app.delete('/notifications/{index}')
async def delete_notification(index: int, current_user: dict = Depends(Security.get_current_user)):
    return await ORM.delete_notification(index)

@app.post('/notification/broadcast')
async def broadcast_subscribes(data: BroadcastDTO, current_user: dict = Depends(Security.get_current_user)):
    title = await ORM.select_lesson_title(data.lesson_id)
    text = f'Пользователь {current_user.get("username")} отправляет приглашение на прохождение урока "{title}".'
    emails = await ORM.select_user_emails(data.user_indices)
    for email in emails:
        email_data = EmailSchema(email_to=email, subject="Новое приглашение!", body=get_notification_mail(text, data.token))
        await email_service.send_email(email_data)
    return await ORM.add_notification_to_users(get_notification_markdown(text, data.token), data.user_indices)


def delete_file(path: str):
    try:
        os.unlink(path)
    except:
        pass

def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

if __name__ == '__main__':
    run_migrations()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)