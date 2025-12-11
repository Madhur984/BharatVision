# backend/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base
import datetime
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    email = Column(String(256), nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    complaints = relationship("Complaint", back_populates="user")

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(256))
    description = Column(Text)
    status = Column(String(64), default="open")  # open, in_progress, resolved, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    metadata = Column(JSON, nullable=True)

    user = relationship("User", back_populates="complaints")

class CrawlerJob(Base):
    __tablename__ = "crawler_jobs"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), nullable=False)
    status = Column(String(64), default="pending")  # pending, running, completed, failed
    result_path = Column(String(2048), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    summary = Column(Text, nullable=True)
