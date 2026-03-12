from fastapi import Depends, HTTPException, status, Query, APIRouter
from sqlalchemy import select, func, insert, update, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import UniqueViolationError, ForeignKeyViolationError
from database import database, engine
from models import companies, reviews, services, projects, users
from schemas import  CompanyCreate, CompanyUpdate, CompanyModel, CompanyListModel, CompanyDetail, ServiceModel, ReviewModel, ProjectModel
from utils import get_current_user, validate_phone_number, validate_email, validate_inn
from typing import List
from decorators import role_required, is_company_owner

router = APIRouter()


# "id": 34, "name": "1", "description": "Правильно описание", "staff": 1, "email": "1@mail.ru", "phone_number": "12345678910", "inn": "7743013901", "site": "1", "services": [{"price": 3,"name": "string"}], "projects": [{"name": "string", "description": "string"}]
# Добавление компании 
@router.post("/", response_model=dict)
@role_required(["admin", "company"])
async def create_update_company(company_data: dict, current_user: dict = Depends(get_current_user)):
    validate_company_data(company_data)

    session = sessionmaker(bind=engine)()

    company_id = company_data.get("id")
    services_data = company_data.pop("services", [])
    projects_data = company_data.pop("projects", [])

    if company_id:
        existing_company = session.execute(select(companies).where(companies.c.id == company_id)).fetchone()
        
        if not existing_company:
            raise HTTPException(
                status_code=404,
                detail="Организация не найдена"
            )

        if current_user["role"] != 'admin' and existing_company.user_id != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав для обновления данной огранизации"
            )

        stmt = update(companies).where(companies.c.id == company_id).values(**company_data)
        try:
            session.execute(stmt)
        except IntegrityError:
            raise HTTPException(status_code=400, detail="У данного пользователя уже есть компания с таким именем")
    else:
        stmt = insert(companies).values(**company_data,
            rating=0, 
            user_id=current_user['user_id'])

        try:
            result = session.execute(stmt)
            company_id = result.inserted_primary_key[0]  # Получаем ID новой компании
        except IntegrityError:
            raise HTTPException(status_code=400, detail="У данного пользователя уже есть компания с таким именем")

    # Синхронизация отзывов
    existing_service_ids = set([r["id"] for r in services_data if "id" in r])
    existing_services = session.execute(select(services).where(services.c.company_id == company_id)).fetchall()

    # Удаляем отзывы, которые больше не включены в запрос
    for service in existing_services:
        if service.id not in existing_service_ids:
            stmt = delete(services).where(services.c.id == service.id)
            session.execute(stmt)

    # Добавляем/обновляем отзывы
    for service_data in services_data:
        if "id" in service_data:
            stmt = update(services).where(services.c.id == service_data["id"]).values(service_data)
        else:
            service_data["company_id"] = company_id
            stmt = insert(services).values(service_data)
        try:
            session.execute(stmt)
        except IntegrityError:
            raise HTTPException(status_code=400, detail="У данного организации уже есть услуга с наименованием " + service_data['name'])

    # Синхронизация проектов
    existing_project_ids = set([p["id"] for p in projects_data if "id" in p])
    existing_projects = session.execute(select(projects).where(projects.c.company_id == company_id)).fetchall()

    # Удаляем проекты, которые больше не включены в запрос
    for project in existing_projects:
        if project.id not in existing_project_ids:
            stmt = delete(projects).where(projects.c.id == project.id)
            session.execute(stmt)

    # Добавляем/обновляем проекты
    for project_data in projects_data:
        if "id" in project_data:
            stmt = update(projects).where(projects.c.id == project_data["id"]).values(project_data)
        else:
            project_data["company_id"] = company_id
            stmt = insert(projects).values(project_data)
        try:
            session.execute(stmt)
        except IntegrityError:
            raise HTTPException(status_code=400, detail="У данного организации уже есть проект с названием " + project_data['name'])
    
    session.commit()
    
    return {"id": company_id, "message": "Компания успешно " + ("обновлена" if company_data.get("id") else "добавлена")}

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
            companies.c.site,
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

@router.get("/{company_id}", response_model=dict)
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

    return {'id': result.id,
        'name' : result.name,
        'rating' : result.rating,
        'description' : result.description,
        'staff' : result.staff,
        'email' :result.email,
        'inn' : result.inn,
        'phone_number' : result.phone_number,
        'user_id' : result.user_id,
        'user_name' : result.user_name,
        'min_price' :result.min_price,
        'max_price' : result.max_price,
        'site' : result.site,
        'services' : list(map(lambda x: ServiceModel(**x), await database.fetch_all(services.select().where(services.c.company_id == company_id)))),
        'projects' : list(map(lambda x: ProjectModel(**x), await database.fetch_all(projects.select().where(projects.c.company_id == company_id)))),
        'reviews' : list(map(lambda x: ReviewModel(**x), await database.fetch_all(reviews.join(users, reviews.c.user_id == users.c.id)
            .select()
            .where(reviews.c.company_id == company_id)
            .with_only_columns(reviews, users.c.name.label("user_name")))))
    }

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
    if not validate_email(company_data['email']):
        raise HTTPException(status_code=400, detail="Невалидная почта")
    if not validate_phone_number(company_data['phone_number']):
        raise HTTPException(status_code=400, detail="Невалидный номер телефона")

    if company_data['inn']:
        (is_valid_inn, error) = validate_inn(company_data['inn'])
        if not is_valid_inn:
            raise HTTPException(status_code=400, detail=error)