from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy import select, func
from asyncpg.exceptions import UniqueViolationError
from database import database
from models import companies, reviews, users
from schemas import ReviewCreate, ReviewUpdate, ReviewModel
from utils import get_current_user
from typing import List
from decorators import role_required

router = APIRouter()

# Добавление отзыва о компании
@router.post("/", response_model=dict)
@role_required(["user", "admin"])
async def create_review(company_id: int, review: ReviewCreate, current_user: dict = Depends(get_current_user)):
    if not 1 <= review.rating <= 5:
        raise HTTPException(status_code=400, detail="Рейтинг может принимать значения от 1 до 5")

    query = reviews.insert().values(
        content=review.content,
        rating=review.rating,
        company_id=company_id,
        user_id=current_user["user_id"],
    )

    try:
        review_id = await database.execute(query)
    except UniqueViolationError:
        raise HTTPException(status_code=400, detail="Отзыв уже был добавлен")

    await update_company_rating(company_id)

    return {"id": review_id, "message": "Отзыв успешно добавлен"}

@router.put("/{review_id}", response_model=ReviewModel)
@role_required(["user", "admin"])
async def update_review(
    company_id: int,
    review_id: int, 
    review_data: ReviewUpdate, 
    current_user: dict = Depends(get_current_user)
):
    # Проверка существования отзыва
    review = await database.fetch_one(reviews.select().where(reviews.c.id == review_id).where(reviews.c.company_id == company_id))
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    if current_user["role"] != "admin" and review["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="У вас нет прав редактировать данный отзыв")

    # Обновление отзыва
    query = reviews.update().where(reviews.c.id == review_id).values(**review_data.dict(exclude_unset=True))
    await database.execute(query)

    await update_company_rating(company_id)

    # Возвращаем обновленные данные отзыва
    updated_review = await database.fetch_one(reviews.join(users, reviews.c.user_id == users.c.id)
        .select()
        .where(reviews.c.id == review_id)
        .with_only_columns(reviews, users.c.name.label("user_name")))

    return updated_review

# Получение всех отзывов о компании
@router.get("/", response_model=List[ReviewModel])
async def get_reviews(company_id: int, current_user: dict = Depends(get_current_user)):
    query = (
        reviews.join(users, reviews.c.user_id == users.c.id)
            .select()
            .where(reviews.c.company_id == company_id)
            .with_only_columns(reviews, users.c.name.label("user_name")) 
    )

    return await database.fetch_all(query)

@router.delete("/{review_id}")
@role_required(["user", "admin"])
async def delete_review(company_id: int, review_id: int, current_user: dict = Depends(get_current_user)):
    review = await database.fetch_one(reviews.select().where(reviews.c.id == review_id).where(reviews.c.company_id == company_id))
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    if current_user["role"] != "admin" and review["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="У вас нет прав для удаления данного отзыва")

    # Удаление отзыва
    query = reviews.delete().where(reviews.c.id == review_id)
    await database.execute(query)

    await update_company_rating(company_id)

    return {"detail": "Отзыв удален"}

# Пересчет рейтинга компании
async def update_company_rating(company_id):
    avg_rating_query = select(func.coalesce(func.avg(reviews.c.rating), 0)).where(reviews.c.company_id == company_id)
    avg_rating = await database.fetch_one(avg_rating_query)
    update_rating_query = companies.update().where(companies.c.id == company_id).values(rating=avg_rating[0])
    await database.execute(update_rating_query)