"""Pydantic 请求/响应模型"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ 认证相关 ============
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    email: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============ 知识库相关 ============
class KBCreateRequest(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None


class KBResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    collection_name: str
    created_at: datetime
    document_count: int = 0

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    kb_id: int
    filename: str
    file_size: int
    chunk_count: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    status: str
    chunks_count: int
    document_id: int
    filename: str


# ============ 对话相关 ============
class ChatRequest(BaseModel):
    question: str
    kb_id: int
    top_k: Optional[int] = 5


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]


class ChatHistoryResponse(BaseModel):
    id: int
    kb_id: int
    question: str
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ 小说写作相关 ============
class NovelCreateRequest(BaseModel):
    title: str = Field(..., max_length=200)
    genre: Optional[str] = None
    description: Optional[str] = None
    style_guide: Optional[str] = None


class NovelResponse(BaseModel):
    id: int
    user_id: int
    title: str
    genre: Optional[str] = None
    description: Optional[str] = None
    outline: Optional[str] = None
    style_guide: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    chapter_count: int = 0

    class Config:
        from_attributes = True


class CharacterCreateRequest(BaseModel):
    name: str = Field(..., max_length=100)
    personality: Optional[str] = None
    background: Optional[str] = None
