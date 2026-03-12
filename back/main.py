from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import select
from asyncpg.exceptions import UniqueViolationError
from database import database
from models import users, services, companies
from schemas import UserCreate, TokenModel, UserModel, UserDetail, UserPasswordUpdate
from utils import get_password_hash, verify_password, create_access_token
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from api import company, project, review, service
from decorators import role_required
from utils import get_current_user, validate_phone_number, validate_email
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(company.router, prefix="/companies", tags=["companies"])
app.include_router(project.router, prefix="/companies/{company_id}/projects", tags=["projects"])
app.include_router(review.router, prefix="/companies/{company_id}/reviews", tags=["reviews"])
app.include_router(service.router, prefix="/companies/{company_id}/services", tags=["services"])

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/register", response_model=dict)
async def register(user: UserCreate):
    if not validate_email(user.email):
        raise HTTPException(status_code=400, detail="Невалидная почта")
    if not validate_phone_number(user.phone_number):
        raise HTTPException(status_code=400, detail="Невалидный номер телефона")

    hashed_password = get_password_hash(user.password)
    query = users.insert().values(email=user.email, hashed_password=hashed_password, name=user.name, role=('company' if user.is_company else 'user'), phone_number=user.phone_number)

    try:
        await database.execute(query)
    except UniqueViolationError:
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")

    return {"message": "Пользователь успешно создан"}

@app.post("/token", response_model=dict)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    query = users.select().where(users.c.email == form_data.username)
    user = await database.fetch_one(query)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Логин/пароль введены неверно")
    access_token = create_access_token(data={"user_id": user["id"],
        "sub": user["email"], 
        "role": user["role"],
        "phone_number": user["phone_number"],
        "name": user["name"]}, expires_delta=timedelta(hours=16))
    return {"access_token": access_token, "id": user["id"], "role": user["role"], "token_type": "bearer"}

@app.get("/users", response_model=list[UserModel])
@role_required(["admin"])
async def get_users(current_user: dict = Depends(get_current_user)):
    query = users.select()
    return await database.fetch_all(query)

@app.put("/users", response_model=dict)
async def change_password(data: UserPasswordUpdate, current_user: dict = Depends(get_current_user)):
    hashed_password = get_password_hash(data.password)
    query = users.update().where(users.c.id == current_user["user_id"]).values(hashed_password=hashed_password)
    await database.execute(query)
    
    return {"message": "Пароль успешно обновлен"}

@app.get("/me", response_model=UserDetail)
async def get_me(current_user: dict = Depends(get_current_user)):
    query = (
        users.join(companies, companies.c.user_id == users.c.id, isouter=True)
            .select()
            .where(users.c.id == current_user['user_id'])
            .with_only_columns(users, companies.c.id.label("company_id")) 
    )

    return await database.fetch_one(query)

@app.put("/me", response_model=dict)
async def change_user(data: dict, current_user: dict = Depends(get_current_user)):
    query = users.update().where(users.c.id == current_user["user_id"]).values(email=data['email'],
        name = data['name'],
        phone_number = data['phone_number'])

    await database.execute(query)
    
    return {"message": "Данные пользователя успешно обновлены"}

@app.get("/services", response_model=List[dict])
async def all_unique_services(current_user: dict = Depends(get_current_user)):
    query = select(services.c.name).distinct()
    return list(map(lambda x: {'name': x['name']}, await database.fetch_all(query))) 