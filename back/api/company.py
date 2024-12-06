from fastapi import Depends, HTTPException, status, Query, APIRouter
from sqlalchemy import select, func
from asyncpg.exceptions import UniqueViolationError, ForeignKeyViolationError
from database import database
from models import companies, reviews, services, projects, users
from schemas import  CompanyCreate, CompanyUpdate, CompanyModel, CompanyListModel, CompanyDetail, ServiceModel, ReviewModel, ProjectModel
from utils import get_current_user, validate_phone_number, validate_email, validate_inn
from typing import List
from decorators import role_required, is_company_owner

router = APIRouter()

# Добавление компании (только для администраторов)
@router.post("/", response_model=dict)
@role_required(["admin"])
async def create_company(company: CompanyCreate, current_user: dict = Depends(get_current_user)):
    validate_company_data(company)

    query = companies.insert().values(name=company.name, 
        rating=0, 
        description=company.description, 
        staff=company.staff, 
        email=company.email, 
        phone_number=company.phone_number, 
        inn=company.inn, 
        user_id=company.user_id)

    try:
        company_id = await database.execute(query)
    except ForeignKeyViolationError:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    except UniqueViolationError:
        raise HTTPException(status_code=400, detail="У данного пользователя уже есть компания с таким именем")

    return {"id": company_id, "message": "Компания успешно добавлена"}

@router.put("/{company_id}", response_model=CompanyModel)
@is_company_owner()
async def update_company(
    company_id: int, 
    company_data: CompanyUpdate, 
    current_user: dict = Depends(get_current_user)
):
    validate_company_data(company_data)

    company = await database.fetch_one(companies.select().where(companies.c.id == company_id))
    if not company:
        raise HTTPException(status_code=404, detail="Организация не найдена")

    # Обновление данных
    query = companies.update().where(companies.c.id == company_id).values(**company_data.dict(exclude_unset=True))

    try:
        await database.execute(query)
    except UniqueViolationError:
        raise HTTPException(status_code=400, detail="У данного пользователя уже есть компания с таким именем")

    # Возвращаем обновленные данные 
    updated_company = await database.fetch_one(companies.select().where(companies.c.id == company_id))
    return updated_company

@router.get("/", response_model=list[CompanyListModel])
async def get_companies(current_user: dict = Depends(get_current_user),
    service_name: List[str] = Query(None),  # Фильтр по названию услуги
    company_name: str = None,  # Фильтр по названию компании
    min_price: float = None,  # Минимальная стоимость услуги
    max_price: float = None,  # Максимальная стоимость услуги
    min_projects: int = None, # Минимальное количество проектов
    min_rating: int = None, # Минимальное количество проектов
    limit: int = 10,          # Количество компаний на странице (пагинация)
    offset: int = 0,          # Смещение для пагинации
):
    # Подзапрос для фильтрации компаний по услугам
    service_filter = select(services.c.company_id).distinct()
    if service_name:
        service_filter = service_filter.where(
            services.c.name.in_([name for name in service_name])
        )
    if min_price is not None:
        service_filter = service_filter.where(services.c.price >= min_price)
    if max_price is not None:
        service_filter = service_filter.where(services.c.price <= max_price)

    # Основной запрос для компаний
    query = (
        select(
            companies.c.id,
            companies.c.name,
            companies.c.rating,
            companies.c.description,
            func.min(services.c.price).label("min_price"),
            func.max(services.c.price).label("max_price"),
            func.count(reviews.c.id.distinct()).label("review_count"),
            func.count(projects.c.id.distinct()).label("project_count"),
            users.c.name.label('user_name')
        )
        .join(services, services.c.company_id == companies.c.id, isouter=True)
        .join(projects, projects.c.company_id == companies.c.id, isouter=True)
        .join(reviews, reviews.c.company_id == companies.c.id, isouter=True)
        .join(users, users.c.id == companies.c.user_id)
        .group_by(companies.c.id, users.c.name)
        .order_by(companies.c.rating.desc())
    )

    # Применение фильтров
    if service_name or min_price is not None or max_price is not None:
        query = query.where(companies.c.id.in_(service_filter))
    if company_name:
        query = query.where(companies.c.name.ilike(f"%{company_name}%"))
    if min_rating:
        query = query.where(companies.c.rating >= min_rating)
    if min_projects is not None:
        query = query.having(func.count(projects.c.id) >= min_projects)

    # Пагинация
    query = query.limit(limit).offset(offset)

    # Выполнение запроса
    result = await database.fetch_all(query)

    # Формирование ответа
    return result

@router.get("/{company_id}", response_model=CompanyDetail)
async def get_company(company_id: int, current_user: dict = Depends(get_current_user)):
    query = (
        companies
            .join(users, users.c.id == companies.c.user_id)
            .join(services, services.c.company_id == company_id, isouter=True)
            .select()
            .where(companies.c.id == company_id)
            .with_only_columns(
                companies, 
                users.c.name.label("user_name"),
                func.min(services.c.price).label("min_price"),
                func.max(services.c.price).label("max_price")  
            )
            .group_by(companies.c.id, users.c.id)  # Группировка по компании и пользователю
    )

    # Выполнение запроса
    result = await database.fetch_one(query)

    if not result:
        raise HTTPException(status_code=404, detail="Организация не найдена")

    return CompanyDetail(id = result.id,
        name = result.name,
        rating = result.rating,
        description = result.description,
        staff = result.staff,
        email = result.email,
        inn = result.inn,
        phone_number = result.phone_number,
        user_id = result.user_id,
        user_name = result.user_name,
        min_price = result.min_price,
        max_price = result.max_price,
        current_user_id = current_user['user_id'],
        is_admin = current_user['role'] == 'admin',
        services = list(map(lambda x: ServiceModel(**x), await database.fetch_all(services.select().where(services.c.company_id == company_id)))),
        projects = list(map(lambda x: ProjectModel(**x), await database.fetch_all(projects.select().where(projects.c.company_id == company_id)))),
        reviews = list(map(lambda x: ReviewModel(**x), await database.fetch_all(reviews.join(users, reviews.c.user_id == users.c.id)
            .select()
            .where(reviews.c.company_id == company_id)
            .with_only_columns(reviews, users.c.name.label("user_name")))))
    )

@router.delete("/{company_id}")
@is_company_owner()
async def delete_company(company_id: int, current_user: dict = Depends(get_current_user)):
    company = await database.fetch_one(companies.select().where(companies.c.id == company_id))
    if not company:
        raise HTTPException(status_code=404, detail="Организация не найдена")

    # Удаление компании
    query = companies.delete().where(companies.c.id == company_id)
    await database.execute(query)
    return {"detail": "Организация удалена"}

def validate_company_data(company_data):
    if not validate_email(company_data.email):
        raise HTTPException(status_code=400, detail="Невалидная почта")
    if not validate_phone_number(company_data.phone_number):
        raise HTTPException(status_code=400, detail="Невалидный номер телефона")

    (is_valid_inn, error) = validate_inn(company_data.inn)
    if not is_valid_inn:
        raise HTTPException(status_code=400, detail=error)