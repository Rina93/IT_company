from fastapi import HTTPException, Depends, status
from functools import wraps
from utils import get_current_user
from database import database

def role_required(allowed_roles: list):
    """
    Декоратор для проверки роли пользователя.
    :param allowed_roles: список допустимых ролей, например ["admin", "company"]
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user or current_user.get("role") not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="У вас нет прав для выполнения данного действия"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def is_company_owner():
    """
    Декоратор для проверки, является ли текущий пользователь владельцем компании.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(company_id: int, *args, **kwargs):
            current_user = kwargs.get("current_user")

            if current_user["role"] != "admin":
                if current_user["role"] == "company":
                    # Проверяем, владеет ли пользователь указанной компанией
                    query = f"SELECT user_id FROM companies WHERE id = :company_id"
                    result = await database.fetch_one(
                        query, values={"company_id": company_id}
                    )

                    if not result:
                        raise HTTPException(
                            status_code=404,
                            detail="Организация не найдена"
                        )

                    if result["user_id"] != current_user["user_id"]:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="У вас нет прав для обновления данной огранизации"
                        )

                else: 
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="У вас нет прав для обновления данной компании"
                    )

            return await func(company_id=company_id, *args, **kwargs)
        return wrapper
    return decorator