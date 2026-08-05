"""用户表 ORM 模型"""
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Column
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    knowledge_bases = relationship(
        "KnowledgeBase", back_populates="user", cascade="all, delete-orphan"
    )
    chat_histories = relationship(
        "ChatHistory", back_populates="user", cascade="all, delete-orphan"
    )
