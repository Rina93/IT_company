from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy import select
from asyncpg.exceptions import UniqueViolationError, ForeignKeyViolationError
from database import database
from models import companies, services
from schemas import ServiceCreate, ServiceUpdate, ServiceModel
from utils import get_current_user
from typing import List
from decorators import is_company_owner

router = APIRouter()

# Добавление услуги компании
@router.post("/", response_model=dict)
@is_company_owner()
async def create_service(company_id: int, service: ServiceCreate, current_user: dict = Depends(get_current_user)):
    query = services.insert().values(name=service.name, price=service.price, company_id=company_id)

    try:
        service_id = await database.execute(query)
    except ForeignKeyViolationError:
        raise HTTPException(status_code=404, detail="Компания не найдена")
    except UniqueViolationError:
        raise HTTPException(status_code=400, detail="У данной организации уже есть услуга с таким наименованием")

    return {"id": service_id, "message": "Услуга успешно добавлена"}

@router.put("/{service_id}", response_model=ServiceModel)
@is_company_owner()
async def update_service(
    company_id: int, 
    service_id: int, 
    service_data: ServiceUpdate, 
    current_user: dict = Depends(get_current_user)
):
    service = await database.fetch_one(services.select().where(services.c.id == service_id).where(services.c.company_id == company_id))
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    # Обновление данных
    query = services.update().where(services.c.id == service_id).values(**service_data.dict(exclude_unset=True))

    try:
        await database.execute(query)
    except UniqueViolationError:
        raise HTTPException(status_code=400, detail="У данного организации уже есть услуга с таким наименованием")

    # Возвращаем обновленные данные  
    updated_service = await database.fetch_one(services.select().where(services.c.id == service_id))
    return updated_service

@router.get("/", response_model=list[ServiceModel])
async def get_services(company_id: int, current_user: dict = Depends(get_current_user)):
    query = services.select().where(services.c.company_id == company_id)
    return await database.fetch_all(query)

@router.delete("/{service_id}")
@is_company_owner()
async def delete_service(company_id: int, service_id: int, current_user: dict = Depends(get_current_user)):
    service = await database.fetch_one(services.select().where(services.c.id == service_id).where(services.c.company_id == company_id))
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    # Удаление Услуги
    query = services.delete().where(services.c.id == service_id)
    await database.execute(query)
    return {"detail": "Услуга удалена"}