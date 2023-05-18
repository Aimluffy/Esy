from fastapi import FastAPI, File, UploadFile, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import uvicorn
from typing import List
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from time import time
from deepface import DeepFace
import os
import jwt

app = FastAPI()

origins = [
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500",
    'http://127.0.0.1:5500/index_2upload.html'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

SECRET_KEY = "your-secret-key"


def change_name(path, image_name, mill, i):
    last = ['id_front', 'id_back', 'face']
    fr = 'png' if image_name.split('.')[1] == 'png' else 'jpg'
    dst = f'{path}/{mill}_{last[i]}.{fr}'
    os.rename(f'{path}/{image_name}', dst)
    return dst


def create_token():
    payload = {"user_id": "user123"}  # Customize the payload as per your requirements
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        return user_id
    except jwt.InvalidTokenError:
        return None


@app.get('/')
async def test(request: Request):
    return templates.TemplateResponse("kyc.html", {"request": request})


@app.post("/uploads-verify")
async def verification_face_and_id_card(
    files: List[UploadFile] = File(...),
    token: str = Depends(create_token)
):
    # Token authentication
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )

    # Verify and process the request for the authenticated user
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    folder = 'face-id'
    mill = int(time() * 1000)
    img_veri = []
    for i, file in enumerate(files):
        destination_file_path = folder + '/' + file.filename  # output file path
        async with aiofiles.open(destination_file_path, 'wb') as out_file:
            while content := await file.read(1024):  # async read file chunk
                await out_file.write(content)

        # rename and saving files
        print(destination_file_path)
        n_img = change_name(folder, file.filename, mill, i)
        img_veri.append(n_img)

    status = DeepFace.verify(img1_path=img_veri[0], img2_path=img_veri[2], model_name="Facenet512")
    output = {"status": "OK", 'verify': status['verified'], "filenames": [file.filename for file in files]}

    # TODO Deep fake detection

    print(output)
    return output


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8005)
    print("running")
