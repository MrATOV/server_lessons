from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
import json
import uvicorn


from src.schemas import *
import src.database.orm as ORM
from src.filesystem import Filesystem
import src.security as Security

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600
)

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
    if data.type == 'image' and data.content == "":
        if not file:
            raise HTTPException(status_code=400, detail="Image file is required")
        fs = Filesystem()
        data.content = await fs.save_image(file, file.filename.split('.')[-1])
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
    if data.type == 'image' and data.content == "":
        if not file:
            raise HTTPException(status_code=400, detail="Image file is required")
        fs = Filesystem()
        data.content = await fs.save_image(file, file.filename.split('.')[-1])

    return await ORM.update_lesson_data(data, index, data_index)


@app.delete("/lesson/{index}/data/{data_index}")
async def delete_lesson_data(index: int, data_index: int):
    return await ORM.delete_lesson_data(data_index)


if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)

@app.get("/image/{filename}")
async def get_image(filename: str):
    fs = Filesystem()
    return FileResponse(fs.get_image(filename), media_type="image/jpeg")

@app.get("/array/{filename}")
async def get_array(filename: str, offset: int = 1, limit: int = 100):
    fs = Filesystem()
    return fs.get_array(filename, offset, limit)

@app.get("/matrix/{filename}")
async def get_matrix(filename: str, page_row: int = 1, limit_row: int = 10, page_col: int = 1, limit_col: int = 10):
    fs = Filesystem()
    return fs.get_matrix(filename, page_row, limit_row, page_col, limit_col)