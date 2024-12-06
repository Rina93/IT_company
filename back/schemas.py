from pydantic import BaseModel
from typing import List, Optional

class UserCreate(BaseModel):
    email: str
    phone_number: str
    password: str
    name: str
    is_company: bool

class TokenModel(BaseModel):
    access_token: str
    token_type: str

class UserModel(BaseModel):
    id: int
    email: str
    phone_number: str
    name: str
    role: str

class UserPasswordUpdate(BaseModel):
    password: str



class ServiceCreate(BaseModel):
    name: str
    price: float

class ServiceUpdate(BaseModel):
    name: str
    price: float

class ServiceModel(BaseModel):
    id: int
    name: str
    price: float


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str]

class ProjectUpdate(BaseModel):
    name: str
    description: Optional[str]

class ProjectModel(BaseModel):
    id: int
    name: str
    description: str


class ReviewCreate(BaseModel):
    content: str
    rating: int

class ReviewUpdate(BaseModel):
    content: str
    rating: float

class ReviewModel(BaseModel):
    id: int
    content: str
    rating: int
    company_id: int
    user_id: int
    user_name: str


class CompanyCreate(BaseModel):
    name: str
    description: str
    staff: int
    email: str
    inn: str
    phone_number: str
    user_id: int

class CompanyUpdate(BaseModel):
    name: str
    staff: int
    description: str
    email: str
    inn: str
    phone_number: str

class CompanyModel(BaseModel):
    id: int
    name: str
    rating: float
    description: str
    staff: int
    email: str
    inn: str
    phone_number: str
    user_id: int

class CompanyDetail(BaseModel):
    id: int
    name: str
    rating: float
    description: str
    staff: int
    email: str
    inn: str
    phone_number: str
    user_id: int
    user_name: str
    current_user_id: int
    is_admin: bool
    min_price: Optional[float]
    max_price: Optional[float]
    services: List[ServiceModel]
    projects: List[ProjectModel]
    reviews: List[ReviewModel]

class CompanyListModel(BaseModel):
    id: int
    name: str
    rating: float
    min_price: Optional[float]
    max_price: Optional[float]
    project_count: int
    review_count: int
    description: str
    user_name: str