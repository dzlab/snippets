
from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    id: int
    username: str = Field(..., min_length=1, max_length=50)
    is_admin: bool = False


class UserProfile(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    bio: str = Field(default="", max_length=500)
    height_cm: int = Field(..., ge=50, le=300)
    weight_kg: float = Field(..., ge=20.0, le=500.0)


class Product(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., ge=0.01)
    stock: int = Field(..., ge=0)
    rating: float = Field(..., ge=0.0, le=5.0)
