from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy import select, func
from asyncpg.exceptions import UniqueViolationError
from database import database
from models import companies, projects
from schemas import ProjectCreate, ProjectUpdate, ProjectModel
from utils import get_current_user
from typing import List
from decorators import is_company_owner

router = APIRouter()

# Добавление проекта компании
@router.post("/", response_model=dict)
@is_company_owner()
async def create_project(company_id: int, project: ProjectCreate, current_user: dict = Depends(get_current_user)):
    query = projects.insert().values(name=project.name, description=project.description, company_id=company_id)

    try:
        project_id = await database.execute(query)
    except UniqueViolationError:
        raise HTTPException(status_code=400, detail="У данной организации уже есть проект с таким наименованием")

    return {"id": project_id, "message": "Проект успешно добавлен"}

@router.put("/{project_id}", response_model=ProjectModel)
@is_company_owner()
async def update_project(
    company_id: int, 
    project_id: int, 
    project_data: ProjectUpdate, 
    current_user: dict = Depends(get_current_user)
):
    project = await database.fetch_one(projects.select().where(projects.c.id == project_id).where(projects.c.company_id == company_id))
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    # Обновление данных
    query = projects.update().where(projects.c.id == project_id).values(**project_data.dict(exclude_unset=True))

    try:
        await database.execute(query)
    except UniqueViolationError:
        raise HTTPException(status_code=400, detail="У данного организации уже есть проект с таким наименованием")

    # Возвращаем обновленные данные  
    updated_project = await database.fetch_one(projects.select().where(projects.c.id == project_id))
    return updated_project

# Получение всех отзывов о компании
@router.get("/", response_model=List[ProjectModel])
async def get_projects(company_id: int, current_user: dict = Depends(get_current_user),):
    query = projects.select().where(projects.c.company_id == company_id)
    return await database.fetch_all(query)

@router.delete("/{project_id}")
@is_company_owner()
async def delete_project(company_id: int, project_id: int, current_user: dict = Depends(get_current_user)):
    project = await database.fetch_one(projects.select().where(projects.c.id == project_id).where(projects.c.company_id == company_id))
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    # Удаление Проекта
    query = projects.delete().where(projects.c.id == project_id)
    await database.execute(query)
    return {"detail": "Проект удален"}