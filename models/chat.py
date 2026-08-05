"""对话历史表 ORM 模型"""
from datetime import datetime
from sqlalchemy import Integer, Text, DateTime, ForeignKey, Column, JSON
from sqlalchemy.orm import relationship

from database import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # 引用来源（JSON 数组）
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_histories")
    kb = relationship("KnowledgeBase", back_populates="chat_histories")
