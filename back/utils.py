from passlib.context import CryptContext
from jose import JWTError, jwt
from jose.exceptions import JWTError
from datetime import datetime, timedelta
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
import re
from fastapi import HTTPException

SECRET_KEY = "secret_key"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        SECRET_KEY = "secret_key"
        ALGORITHM = "HS256"
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось проверить учетные данные",
        )

def validate_phone_number(phone):
    """Проверяет номер телефона на соответствие международному формату"""
    if phone == '':
        return True
    pattern = r'^\+?\d{10,15}$'  # Разрешает + в начале и 10-15 цифр
    return re.match(pattern, phone) is not None

def validate_email(email):
    """Проверяет, является ли email корректным"""
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def validate_inn(inn):
    """Валидация ИНН (идентификационного номера налогоплательщика)"""
    if not inn.isdigit():
        return False, "ИНН должен состоять только из цифр"
    
    if len(inn) not in (10, 12):
        return False, "ИНН должен быть длиной 10 или 12 символов"

    # Проверка контрольной суммы для 10-значного ИНН
    if len(inn) == 10:
        factors = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum = sum(int(inn[i]) * factors[i] for i in range(9)) % 11 % 10
        if checksum != int(inn[-1]):
            return False, "Контрольная сумма не совпадает для ИНН длиной 10"

    # Проверка контрольной суммы для 12-значного ИНН
    if len(inn) == 12:
        factors_11 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0]
        factors_12 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0]
        checksum_11 = sum(int(inn[i]) * factors_11[i] for i in range(11)) % 11 % 10
        checksum_12 = sum(int(inn[i]) * factors_12[i] for i in range(12)) % 11 % 10
        if checksum_11 != int(inn[10]) or checksum_12 != int(inn[11]):
            return False, "Контрольная сумма не совпадает для ИНН длиной 12"

    return True, ""