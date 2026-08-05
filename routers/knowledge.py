"""知识库管理路由：创建 / 列表 / 删除 / 上传文档 / 文档列表"""
import os
import time
from uuid import uuid4
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_user
from models.user import User
from models.knowledge import KnowledgeBase, Document
from models.schemas import (
    KBCreateRequest, KBResponse, DocumentResponse, UploadResponse,
)
from core.rag_engine import RAGEngine
from core.vector_store import remove_vector_store, get_vector_store
from config import UPLOAD_DIR

router = APIRouter(prefix="/api/knowledge", tags=["知识库管理"])


def _get_owned_kb(kb_id: int, user: User, db: Session) -> KnowledgeBase:
    """获取属于当前用户的知识库，不存在或不归属则 404/403"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
    if kb.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该知识库")
    return kb


@router.post("/create", response_model=KBResponse, status_code=status.HTTP_201_CREATED)
def create_kb(req: KBCreateRequest, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    """创建知识库"""
    kb = KnowledgeBase(
        user_id=user.id,
        name=req.name,
        description=req.description,
        collection_name=f"kb_{uuid4().hex[:16]}",
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return KBResponse.model_validate({**kb.__dict__, "document_count": 0})


@router.get("/list", response_model=List[KBResponse])
def list_kbs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户的知识库列表"""
    kbs = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.user_id == user.id)
        .order_by(KnowledgeBase.created_at.desc())
        .all()
    )
    result = []
    for kb in kbs:
        doc_count = db.query(Document).filter(Document.kb_id == kb.id).count()
        result.append(KBResponse.model_validate({**kb.__dict__, "document_count": doc_count}))
    return result


@router.delete("/{kb_id}")
def delete_kb(kb_id: int, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    """删除知识库（含数据库记录 + 向量索引）"""
    kb = _get_owned_kb(kb_id, user, db)

    # 1. 删除向量索引文件
    remove_vector_store(kb.collection_name)
    # 2. 删除数据库记录（文档、对话历史通过级联删除）
    db.delete(kb)
    db.commit()
    return {"status": "success", "message": "知识库已删除"}


@router.post("/{kb_id}/upload", response_model=UploadResponse)
async def upload_documents(
    kb_id: int,
    files: List[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传文档到知识库（支持多文件，自动分块 + 向量化）"""
    kb = _get_owned_kb(kb_id, user, db)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    rag_engine = RAGEngine(kb.collection_name)
    total_chunks = 0
    last_doc_id = 0
    last_filename = ""

    for file in files:
        safe_name = f"{int(time.time())}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)
        content = await file.read()
        file_size = len(content)

        # 保存文件到磁盘
        with open(file_path, "wb") as f:
            f.write(content)

        # 先创建数据库记录获取文档ID
        doc = Document(
            kb_id=kb.id,
            filename=file.filename,
            file_size=file_size,
            chunk_count=0,
            file_path=file_path,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # 加载、分块、向量化、存储（传入文档ID用于后续删除定位）
        # 如果处理失败，回滚数据库记录并删除磁盘文件
        try:
            result = await rag_engine.load_documents(file_path, document_id=doc.id, original_filename=file.filename)
            chunks = result["chunks_count"]
            total_chunks += chunks
        except Exception as e:
            # 处理失败：删除 DB 记录和磁盘文件，不让残留
            db.delete(doc)
            db.commit()
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")

        # 更新分块数
        doc.chunk_count = chunks
        db.commit()
        db.refresh(doc)

        last_doc_id = doc.id
        last_filename = file.filename

    return UploadResponse(
        status="success",
        chunks_count=total_chunks,
        document_id=last_doc_id,
        filename=last_filename,
    )


@router.get("/{kb_id}/documents", response_model=List[DocumentResponse])
def list_documents(kb_id: int, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """获取知识库下的文档列表"""
    kb = _get_owned_kb(kb_id, user, db)
    docs = (
        db.query(Document)
        .filter(Document.kb_id == kb.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return docs


@router.delete("/{kb_id}/documents/{doc_id}")
def delete_document(kb_id: int, doc_id: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """删除单个文档（数据库记录 + 向量分块 + 磁盘文件）"""
    kb = _get_owned_kb(kb_id, user, db)

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.kb_id == kb.id,
    ).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 1. 删除向量分块（先按 document_id 删，再按 filename 兜底删旧数据）
    vector_store = get_vector_store(kb.collection_name)
    deleted_chunks = vector_store.delete_document_chunks(doc_id)
    # 旧数据可能没有 document_id，用 filename 兜底再删一次
    deleted_chunks += vector_store.delete_by_filename(doc.filename)

    # 2. 删除磁盘文件
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError:
            pass

    # 3. 删除数据库记录
    db.delete(doc)
    db.commit()

    return {"status": "success", "message": "文档已删除", "deleted_chunks": deleted_chunks}
