"""对话路由：关联知识库问答 / 流式问答 / 历史记录 CRUD"""
import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db, SessionLocal
from deps import get_current_user
from models.user import User
from models.knowledge import KnowledgeBase
from models.chat import ChatHistory
from models.schemas import ChatRequest, ChatResponse, ChatHistoryResponse
from core.rag_engine import RAGEngine

router = APIRouter(prefix="/api/chat", tags=["对话"])


def _get_owned_kb(kb_id: int, user: User, db: Session) -> KnowledgeBase:
    """校验知识库归属"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if kb is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
    if kb.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该知识库")
    return kb


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    """普通问答（关联知识库，结果写入历史）"""
    kb = _get_owned_kb(req.kb_id, user, db)
    rag_engine = RAGEngine(kb.collection_name)

    result = await rag_engine.query(req.question, req.top_k)

    # 写入对话历史
    history = ChatHistory(
        user_id=user.id,
        kb_id=kb.id,
        question=req.question,
        answer=result["answer"],
        sources=result["sources"],
    )
    db.add(history)
    db.commit()

    return result


@router.post("/stream")
async def chat_stream(req: ChatRequest, user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """流式问答（SSE），完成后写入历史"""
    kb = _get_owned_kb(req.kb_id, user, db)
    rag_engine = RAGEngine(kb.collection_name)

    question = req.question
    kb_id = kb.id
    user_id = user.id

    async def generate():
        sources = []
        answer_buf = []

        try:
            async for chunk in rag_engine.query_stream(question, req.top_k):
                if chunk.startswith("[SOURCES]"):
                    try:
                        sources = json.loads(chunk[len("[SOURCES]"):])
                    except Exception:
                        sources = []
                    yield f"data: {json.dumps({'type': 'sources', 'data': sources}, ensure_ascii=False)}\n\n"
                else:
                    answer_buf.append(chunk)
                    yield f"data: {json.dumps({'type': 'chunk', 'data': chunk}, ensure_ascii=False)}\n\n"
        except Exception as e:
            error_msg = f"处理出错: {str(e)}"
            logging.error(f"流式问答异常: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'data': error_msg}, ensure_ascii=False)}\n\n"
        finally:
            if answer_buf:
                session = SessionLocal()
                try:
                    history = ChatHistory(
                        user_id=user_id,
                        kb_id=kb_id,
                        question=question,
                        answer="".join(answer_buf),
                        sources=sources,
                    )
                    session.add(history)
                    session.commit()
                except Exception as e:
                    logging.error(f"保存对话历史失败: {e}")
                finally:
                    session.close()

            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/history", response_model=List[ChatHistoryResponse])
def get_history(
    kb_id: Optional[int] = Query(None, description="按知识库过滤"),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取对话历史（可按知识库过滤）"""
    q = db.query(ChatHistory).filter(ChatHistory.user_id == user.id)
    if kb_id is not None:
        # 同时校验该知识库归属
        _get_owned_kb(kb_id, user, db)
        q = q.filter(ChatHistory.kb_id == kb_id)
    items = q.order_by(ChatHistory.created_at.desc()).limit(limit).all()
    return items


@router.delete("/history/{history_id}")
def delete_history(history_id: int, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """删除一条对话记录"""
    item = db.query(ChatHistory).filter(ChatHistory.id == history_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在")
    if item.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该记录")
    db.delete(item)
    db.commit()
    return {"status": "success", "message": "记录已删除"}


@router.delete("/history")
def clear_history(
    kb_id: int = Query(..., description="知识库 ID"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """清空指定知识库的所有对话历史"""
    _get_owned_kb(kb_id, user, db)
    deleted = db.query(ChatHistory).filter(
        ChatHistory.user_id == user.id,
        ChatHistory.kb_id == kb_id,
    ).delete()
    db.commit()
    return {"status": "success", "message": f"已清空 {deleted} 条记录"}
