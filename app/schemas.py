from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from app.models import PostStatus, PostTone

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Base User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class User(UserInDB):
    pass

# Persona schemas
class PersonaBase(BaseModel):
    name: str
    description: Optional[str] = None

class PersonaCreate(PersonaBase):
    pass

class PersonaUpdate(PersonaBase):
    name: Optional[str] = None

class PersonaInDB(PersonaBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Persona(PersonaInDB):
    pass

# LinkedIn Account schemas
class LinkedInAccountBase(BaseModel):
    profile_id: str
    profile_url: str

class LinkedInAccountCreate(LinkedInAccountBase):
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None

class LinkedInAccountUpdate(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    profile_url: Optional[str] = None

class LinkedInAccountInDB(LinkedInAccountBase):
    id: int
    user_id: int
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class LinkedInAccount(LinkedInAccountInDB):
    pass

# Post schemas
class PostBase(BaseModel):
    content: str
    tone: PostTone
    persona_id: Optional[int] = None
    linkedin_account_id: Optional[int] = None
    source_type: Optional[str] = None
    source_data: Optional[Dict[str, Any]] = None

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    content: Optional[str] = None
    tone: Optional[PostTone] = None
    status: Optional[PostStatus] = None
    scheduled_time: Optional[datetime] = None
    persona_id: Optional[int] = None
    linkedin_account_id: Optional[int] = None

class PostInDB(PostBase):
    id: int
    user_id: int
    status: PostStatus
    scheduled_time: Optional[datetime] = None
    published_time: Optional[datetime] = None
    linkedin_post_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Post(PostInDB):
    pass

# Post Analytics schemas
class PostAnalyticsBase(BaseModel):
    impressions: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    clicks: int = 0

class PostAnalyticsCreate(PostAnalyticsBase):
    post_id: int

class PostAnalyticsUpdate(PostAnalyticsBase):
    pass

class PostAnalyticsInDB(PostAnalyticsBase):
    id: int
    post_id: int
    last_updated: datetime

    class Config:
        orm_mode = True

class PostAnalytics(PostAnalyticsInDB):
    pass

# Content Generation schemas
class ContentGenerationRequest(BaseModel):
    source_type: str = Field(..., description="Type of source: 'bullet_points', 'file', or 'url'")
    source_data: Dict[str, Any] = Field(..., description="Source data in appropriate format based on source_type")
    tone: PostTone
    persona_id: Optional[int] = None
    linkedin_account_id: Optional[int] = None

class ContentGenerationResponse(BaseModel):
    content: str
    tone: PostTone
    source_type: str
    source_data: Dict[str, Any]

# Scheduling schemas
class SchedulePostRequest(BaseModel):
    post_id: int
    scheduled_time: datetime
    linkedin_account_id: int

class SchedulePostResponse(BaseModel):
    post_id: int
    scheduled_time: datetime
    status: PostStatus

# Login schema
class LoginRequest(BaseModel):
    username: str
    password: str