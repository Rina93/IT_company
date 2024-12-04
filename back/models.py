from sqlalchemy import Table, Column, Integer, String, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from database import metadata

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255), unique=True, nullable=False),
    Column("phone_number", String(15), nullable=False),
    Column("hashed_password", String(255), nullable=False),
    Column("role", String(20), nullable=False),  # "user", "company", "admin"
    Column("name", String(50)),
)

companies = Table(
    "companies",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("rating", Float, default=0),
    Column("description", Text),
    Column("staff", Integer, nullable=False),
    Column("email", String(255), nullable=False),
    Column("inn", String(12), nullable=False),
    Column("phone_number", String(15), nullable=False),
    Column("user_id", Integer, ForeignKey("users.id")),
)

services = Table(
    "services",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("price", Float, nullable=False),
    Column("company_id", Integer, ForeignKey("companies.id")),
)

projects = Table(
    "projects",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    Column("company_id", Integer, ForeignKey("companies.id")),
)

reviews = Table(
    "reviews",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("content", Text, nullable=False),
    Column("rating", Integer, nullable=False),
    Column("company_id", Integer, ForeignKey("companies.id")),
    Column("user_id", Integer, ForeignKey("users.id")),
)
