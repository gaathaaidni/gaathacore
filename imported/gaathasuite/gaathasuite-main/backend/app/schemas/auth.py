from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    organization_id: Optional[int] = None
    is_active: bool
    role: str
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    email_verified: bool
    email_verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Enable ORM mode

class UserInDB(UserRead):
    password_hash: str

class OnboardingCreate(BaseModel):
    org_name: str
    user_email: EmailStr
    password: str

class OrganizationRegistration(BaseModel):
    """Schema for organization registration with expanded fields."""
    organizationName: str
    website: Optional[str] = None
    industry: str
    companySize: str
    phone: Optional[str] = None
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    """Schema for login with username and password."""
    username: str
    password: str
    remember_me: Optional[bool] = False


class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = None
    department: Optional[str] = None
    organization_id: Optional[int] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None