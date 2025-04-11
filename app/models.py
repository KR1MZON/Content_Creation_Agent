from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime

Base = declarative_base()

class PostStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"

class PostTone(str, enum.Enum):
    PROFESSIONAL = "professional"
    INSPIRATIONAL = "inspirational"
    STORYTELLING = "storytelling"
    HUMOROUS = "humorous"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    posts = relationship("Post", back_populates="author")
    personas = relationship("Persona", back_populates="user")
    linkedin_accounts = relationship("LinkedInAccount", back_populates="user")

class Persona(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="personas")
    posts = relationship("Post", back_populates="persona")

class LinkedInAccount(Base):
    __tablename__ = "linkedin_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    access_token = Column(String)
    refresh_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    profile_id = Column(String)
    profile_url = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="linkedin_accounts")
    posts = relationship("Post", back_populates="linkedin_account")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=True)
    linkedin_account_id = Column(Integer, ForeignKey("linkedin_accounts.id"), nullable=True)
    content = Column(Text)
    tone = Column(Enum(PostTone))
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT)
    scheduled_time = Column(DateTime, nullable=True)
    published_time = Column(DateTime, nullable=True)
    source_type = Column(String, nullable=True)  # "bullet_points", "file", "url"
    source_data = Column(JSON, nullable=True)  # Store original source data
    linkedin_post_id = Column(String, nullable=True)  # ID of the post on LinkedIn
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    author = relationship("User", back_populates="posts")
    persona = relationship("Persona", back_populates="posts")
    linkedin_account = relationship("LinkedInAccount", back_populates="posts")
    analytics = relationship("PostAnalytics", back_populates="post", uselist=False)

class PostAnalytics(Base):
    __tablename__ = "post_analytics"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), unique=True)
    impressions = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    last_updated = Column(DateTime, default=func.now())
    
    # Relationships
    post = relationship("Post", back_populates="analytics")