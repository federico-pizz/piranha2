from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr
    preferences: Dict[str, Any] = {}


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    title: str
    description: Optional[str]
    price_eur: float
    region: Optional[str]
    city: Optional[str]
    condition: str
    year: Optional[int]
    brand: Optional[str]
    category: str


class ProductCreate(ProductBase):
    source_url: str
    source_name: str


class Product(ProductBase):
    id: UUID
    source_url: str
    source_name: str
    scraped_at: datetime
    verified: bool
    
    class Config:
        from_attributes = True


class RecommendationBase(BaseModel):
    product_id: UUID
    score: float


class RecommendationCreate(RecommendationBase):
    user_id: UUID


class Recommendation(RecommendationBase):
    id: UUID
    user_id: UUID
    generated_at: datetime
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class PreferenceUpdate(BaseModel):
    preferences: Dict[str, Any]