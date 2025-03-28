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
from src.report import generate_performance_report


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600
)

s3_client = S3Client()
fs = Filesystem()

@app.get('/users')
async def get_users():
    users = await ORM.select_users()
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

@app.delete('/users/{index}')
async def delete_user(index: int):
    return ORM.delete_user(index)

@app.post('/lesson')
async def insert_lesson(lesson: LessonListDTO):
    return await ORM.insert_lesson(lesson)

@app.get("/lesson/list")
async def get_lesson_list():
    lessons = await ORM.select_lesson_list()
    return lessons

@app.delete("/lesson/{index}")
async def delete_lesson(index: int):
    return await ORM.delete_lesson(index)

@app.post('/lesson/{index}/data')
async def insert_lesson_data(index: int, lesson_data: str = Form(...), file: Optional[UploadFile] = File(None)):
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
async def delete_lesson_data(index: int, data_index: int):
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
async def get_array_data(filename: str, offset: int = 1, limit: int = 100, current_user: dict = Depends(Security.get_current_user)):
    temp_file_path = s3_client.get_temporary_file(current_user["id"], filename)
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
async def get_matrix_data(filename: str, page_row: int = 1, limit_row: int = 10, page_col: int = 1, limit_col: int = 10, current_user: dict = Depends(Security.get_current_user)):
    temp_file_path = s3_client.get_temporary_file(current_user["id"], filename)
    return fs.get_matrix(temp_file_path, page_row, limit_row, page_col, limit_col)

@app.post("/data/text/content")
async def create_text_data(data: TextDTO, current_user: dict = Depends(Security.get_current_user)):
    filename = fs.create_text(data)
    filepath = s3_client.upload_file_from_path(filename, current_user["id"])
    return await ORM.add_default_data(filepath, "text", current_user.get("id"))

@app.get("/data/text/{filename}")
async def get_text_data(filename: str, current_user: dict = Depends(Security.get_current_user)):
    temp_file_path = s3_client.get_temporary_file(current_user["id"], filename)
    return fs.get_text_data(temp_file_path)

@app.post("/data/{type}")
async def create_image_data(type: str, file: UploadFile = File(...), current_user: dict = Depends(Security.get_current_user)):
    filepath = s3_client.upload_file_private(file, current_user["id"])
    return await ORM.add_default_data(filepath, type, current_user.get("id"))

@app.get("/data/image/{filename}")
async def get_data_image(filename: str, background_tasks: BackgroundTasks, current_user: dict = Depends(Security.get_current_user)):
    local_file_path = s3_client.get_temporary_file(current_user["id"], filename)
    media_type, _ = mimetypes.guess_type(filename)
    if not media_type:
        media_type = "image/jpeg"
    background_tasks.add_task(delete_file, local_file_path)
    return FileResponse(local_file_path, media_type=media_type)

@app.get("/data/audio/{filename}")
async def get_data_image(filename: str, background_tasks: BackgroundTasks, current_user: dict = Depends(Security.get_current_user)):
    local_file_path = s3_client.get_temporary_file(current_user["id"], filename)
    media_type, _ = mimetypes.guess_type(filename)
    if not media_type:
        media_type = "audio/mp3"
    background_tasks.add_task(delete_file, local_file_path)
    return FileResponse(local_file_path, media_type=media_type)

@app.get("/data/video/{filename}")
async def get_data_image(filename: str, background_tasks: BackgroundTasks, current_user: dict = Depends(Security.get_current_user)):
    local_file_path = s3_client.get_temporary_file(current_user["id"], filename)
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