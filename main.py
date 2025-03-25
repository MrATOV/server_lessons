from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
import json
import uvicorn
from alembic.config import Config
from alembic import command
import mimetypes


from src.schemas import *
import src.database.orm as ORM
from src.filesystem import Filesystem
import src.security as Security
from src.s3_client import S3Client


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

@app.post("/array/random")
async def create_random_array(data: RandomArrayDTO, current_user: dict = Depends(Security.get_current_user)):
    filename = fs.create_random_array(data)
    s3_client.upload_file_from_path(filename, current_user["id"])

@app.post("/array/order")
async def create_order_array(data: OrderArrayDTO, current_user: dict = Depends(Security.get_current_user)):
    filename = fs.create_order_array(data)
    s3_client.upload_file_from_path(filename, current_user["id"])

@app.get("/array/{filename}")
async def get_array_data(filename: str, offset: int = 1, limit: int = 100, current_user: dict = Depends(Security.get_current_user)):
    temp_file_path = s3_client.get_temporary_file(current_user["id"], filename)
    return fs.get_array(temp_file_path, offset, limit)

@app.post("/matrix/random")
async def create_random_matrix(data: RandomMatrixDTO, current_user: dict = Depends(Security.get_current_user)):
    filename = fs.create_random_matrix(data)
    s3_client.upload_file_from_path(filename, current_user["id"])

@app.post("/matrix/order")
async def create_order_matrix(data: OrderMatrixDTO, current_user: dict = Depends(Security.get_current_user)):
    filename = fs.create_order_matrix(data)
    s3_client.upload_file_from_path(filename, current_user["id"])

@app.get("/matrix/{filename}")
async def get_matrix_data(filename: str, page_row: int = 1, limit_row: int = 10, page_col: int = 1, limit_col: int = 10, current_user: dict = Depends(Security.get_current_user)):
    temp_file_path = s3_client.get_temporary_file(current_user["id"], filename)
    return fs.get_matrix(temp_file_path, page_row, limit_row, page_col, limit_col)

@app.post("/text_data/")
async def create_text_file(data: TextDTO, current_user: dict = Depends(Security.get_current_user)):
    filename = fs.create_text(data)
    s3_client.upload_file_from_path(filename, current_user["id"])

@app.get("/text_data/{filename}")
async def get_text_data(filename: str, current_user: dict = Depends(Security.get_current_user)):
    temp_file_path = s3_client.get_temporary_file(current_user["id"], filename)
    return fs.get_text_data(temp_file_path)

@app.get("/image/{lesson_id}/{filename}")
async def get_image(lesson_id: str, filename: str):
    local_file_path = s3_client.get_file("image", lesson_id, filename)
    media_type, _ = mimetypes.guess_type(filename)
    if not media_type:
        media_type = "image/jpeg"
    return FileResponse(local_file_path, media_type=media_type)

@app.get("/audio/{lesson_id}/{filename}")
async def get_audio(lesson_id: str, filename: str):
    local_file_path = s3_client.get_file("audio", lesson_id, filename)
    media_type, _ = mimetypes.guess_type(filename)
    if not media_type:
        media_type = "video/mp4"
    return FileResponse(local_file_path, media_type=media_type)

@app.get("/video/{lesson_id}/{filename}")
async def get_video(lesson_id: str, filename: str):
    local_file_path = s3_client.get_file("video", lesson_id, filename)
    media_type, _ = mimetypes.guess_type(filename)
    if not media_type:
        media_type = "audio/mp3"
    return FileResponse(local_file_path, media_type=media_type)


def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

if __name__ == '__main__':
    run_migrations()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)