from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Optional
import json
import uvicorn
import mimetypes
import os

from src.schemas import *
import src.database.orm as ORM
import src.security as Security
from src.s3_client import S3Client
from src.redis_client import RedisClient

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

@app.post('/lesson')
async def insert_lesson(lesson: LessonListDTO, current_user: dict = Depends(Security.get_current_user)):
    return await ORM.insert_lesson(lesson, current_user.get("id"))

@app.get("/lesson/list/own")
async def get_lesson_list_own(
    title: Optional[str] = Query(None),
    total_count: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(Security.get_current_user)
):
    lessons = await ORM.select_lesson_list_own(current_user.get("id"), title, total_count, page, page_size)
    return lessons

@app.get("/lesson/list/public")
async def get_lesson_list_public(
    title: Optional[str] = Query(None),
    total_count: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    lessons = await ORM.select_lesson_list_public(title, total_count, page, page_size)
    return lessons

@app.get("/lesson/list/admin")
async def get_lesson_list_admin(
    title: Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    total_count: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(Security.get_current_user)
):
    if (current_user.get('role') != 'admin'):
        raise HTTPException(403, 'Not administrator')
    lessons = await ORM.select_lesson_list_admin(title, username, email, total_count, page, page_size)
    return lessons

@app.get('/lessons/users')
async def get_user_lessons(
    current_user: dict = Depends(Security.get_current_user),
    title: Optional[str] = Query(None),
    total_count: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    return await ORM.select_user_lessons(current_user.get("id"), title, total_count, page, page_size)

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
async def get_lesson_data(
    index: int,
    total_count: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    is_editing: bool = Query(False)
):
    return await ORM.select_lesson_data(index, total_count, page, page_size, is_editing)

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


def delete_file(path: str):
    try:
        os.unlink(path)
    except:
        pass

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)