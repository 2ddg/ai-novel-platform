"""知识库表 + 文档表 ORM 模型"""
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Column
from sqlalchemy.orm import relationship

from database import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    # 对应向量库中的 collection 名称（每个知识库一个独立 FAISS 索引）
    collection_name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="knowledge_bases")
    documents = relationship(
        "Document", back_populates="kb", cascade="all, delete-orphan"
    )
    chat_histories = relationship(
        "ChatHistory", back_populates="kb", cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    chunk_count = Column(Integer, nullable=False, default=0)
    # 存储在服务器上的实际路径
    file_path = Column(String(512), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    kb = relationship("KnowledgeBase", back_populates="documents")
