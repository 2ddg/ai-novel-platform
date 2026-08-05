"""小说写作路由：项目管理 / 角色 / 大纲 / 章节 / 记忆 / 导入 / 审阅"""
import json
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_user
from models.user import User
from models.novel import Novel, Character, Chapter, Memory, Foreshadowing, Timeline, Version
from models.schemas import NovelCreateRequest, NovelResponse, CharacterCreateRequest
from core.novel_engine import NovelEngine

router = APIRouter(prefix="/api/novel", tags=["小说写作"])

logger = logging.getLogger(__name__)


def _get_owned_novel(novel_id: int, user: User, db: Session) -> Novel:
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if novel is None:
        raise HTTPException(status_code=404, detail="小说项目不存在")
    if novel.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权操作该项目")
    return novel


def _orm_to_dict(obj):
    """安全将 SQLAlchemy ORM 对象转为纯字典（排除 relationship 字段）"""
    if obj is None:
        return None
    result = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        result[col.name] = val
    return result


def _orm_list(query):
    """将查询结果列表转为纯字典列表"""
    return [_orm_to_dict(item) for item in query]


# ============ 小说项目 CRUD ============

@router.post("", response_model=NovelResponse, status_code=status.HTTP_201_CREATED)
def create_novel(req: NovelCreateRequest, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """创建小说项目"""
    novel = Novel(
        user_id=user.id,
        title=req.title,
        genre=req.genre,
        description=req.description,
        style_guide=req.style_guide,
    )
    db.add(novel)
    db.commit()
    db.refresh(novel)
    return NovelResponse.model_validate({**novel.__dict__, "chapter_count": 0})


@router.get("", response_model=List[NovelResponse])
def list_novels(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户的小说项目列表"""
    novels = (
        db.query(Novel)
        .filter(Novel.user_id == user.id)
        .order_by(Novel.created_at.desc())
        .all()
    )
    result = []
    for n in novels:
        ch_count = db.query(Chapter).filter(Chapter.novel_id == n.id).count()
        result.append(NovelResponse.model_validate({**n.__dict__, "chapter_count": ch_count}))
    return result


@router.get("/{novel_id}", response_model=NovelResponse)
def get_novel(novel_id: int, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    """获取小说详情"""
    novel = _get_owned_novel(novel_id, user, db)
    ch_count = db.query(Chapter).filter(Chapter.novel_id == novel.id).count()
    return NovelResponse.model_validate({**novel.__dict__, "chapter_count": ch_count})


@router.put("/{novel_id}", response_model=NovelResponse)
def update_novel(novel_id: int, req: dict, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """更新小说基本信息（支持部分更新）"""
    novel = _get_owned_novel(novel_id, user, db)
    if "title" in req:
        novel.title = req["title"]
    if "genre" in req:
        novel.genre = req["genre"]
    if "description" in req:
        novel.description = req["description"]
    if "style_guide" in req:
        novel.style_guide = req["style_guide"]
    if "outline" in req:
        novel.outline = req["outline"]
    db.commit()
    db.refresh(novel)
    ch_count = db.query(Chapter).filter(Chapter.novel_id == novel.id).count()
    return NovelResponse.model_validate({**novel.__dict__, "chapter_count": ch_count})


@router.delete("/{novel_id}")
def delete_novel(novel_id: int, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """删除小说项目"""
    novel = _get_owned_novel(novel_id, user, db)
    db.delete(novel)
    db.commit()
    return {"status": "success", "message": "小说项目已删除"}


# ============ 角色管理 ============

@router.post("/{novel_id}/characters", status_code=status.HTTP_201_CREATED)
def create_character(novel_id: int, req: CharacterCreateRequest,
                     user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """创建/更新角色"""
    novel = _get_owned_novel(novel_id, user, db)
    char = Character(
        novel_id=novel.id,
        name=req.name,
        personality=req.personality,
        background=req.background,
    )
    db.add(char)
    db.commit()
    db.refresh(char)
    return char


@router.get("/{novel_id}/characters")
def list_characters(novel_id: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """获取角色列表"""
    novel = _get_owned_novel(novel_id, user, db)
    return _orm_list(db.query(Character).filter(Character.novel_id == novel.id).all())


@router.put("/{novel_id}/characters/{char_id}")
def update_character(novel_id: int, char_id: int, req: CharacterCreateRequest,
                     user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """更新角色"""
    novel = _get_owned_novel(novel_id, user, db)
    char = db.query(Character).filter(Character.id == char_id, Character.novel_id == novel.id).first()
    if char is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    char.name = req.name
    char.personality = req.personality
    char.background = req.background
    db.commit()
    db.refresh(char)
    return char


@router.delete("/{novel_id}/characters/{char_id}")
def delete_character(novel_id: int, char_id: int, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """删除角色"""
    novel = _get_owned_novel(novel_id, user, db)
    char = db.query(Character).filter(Character.id == char_id, Character.novel_id == novel.id).first()
    if char is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    db.delete(char)
    db.commit()
    return {"status": "success", "message": "角色已删除"}


# ============ 大纲生成 ============

@router.post("/{novel_id}/generate-outline")
async def generate_outline(novel_id: int, req: dict = Body(default={}),
                          user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    novel = _get_owned_novel(novel_id, user, db)

    chars = db.query(Character).filter(Character.novel_id == novel.id).all()
    chars_text = "\n".join([f"- {c.name}：{c.personality or ''}" for c in chars])

    ideas = req.get("ideas", "").strip() if req else ""

    outline = await NovelEngine.generate_outline(
        title=novel.title,
        genre=novel.genre,
        description=novel.description,
        characters=chars_text,
        style_guide=novel.style_guide,
        user_ideas=ideas,
    )

    novel.outline = outline
    db.commit()
    db.refresh(novel)
    return {"status": "success", "outline": outline}


# ============ 章节写作 ============

@router.post("/{novel_id}/chapters/generate")
async def generate_chapter(novel_id: int, req: dict,
                           user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    """生成单个章节（非流式）+ 写后审计 + 门禁 + 自动重写"""
    novel = _get_owned_novel(novel_id, user, db)
    chapter_num = req.get("chapter_num", 1)
    chapter_outline = req.get("chapter_outline", "")
    title = req.get("title", f"第{chapter_num}章")

    chars = db.query(Character).filter(Character.novel_id == novel.id).all()
    chars_text = "\n".join([f"- {c.name}：{c.personality or ''}" for c in chars])

    # 注入角色当前状态
    char_states_text = NovelEngine.format_character_states(chars)
    if char_states_text:
        chars_text += f"\n\n【角色当前状态】\n{char_states_text}"

    # 获取合并记忆：所有章节记忆 + 全局记忆
    all_memories = db.query(Memory).filter(Memory.novel_id == novel.id).all()
    memory_parts = []
    for m in all_memories:
        if m.chapter_num:
            memory_parts.append(f"第{m.chapter_num}章后：{m.content}")
        else:
            memory_parts.append(f"全局：{m.content}")
    memory_text = "\n".join(memory_parts) if memory_parts else "（初始状态）"

    # 查询未回收伏笔，注入到记忆中
    pending_foreshadowings = db.query(Foreshadowing).filter(
        Foreshadowing.novel_id == novel.id, Foreshadowing.status == "pending"
    ).all()
    if pending_foreshadowings:
        foreshadow_text = NovelEngine.format_pending_foreshadowings(pending_foreshadowings)
        memory_text += f"\n\n【未回收伏笔（请注意适时回收）】\n{foreshadow_text}"

    # 查询最近时间线，注入到记忆中
    all_timelines = db.query(Timeline).filter(Timeline.novel_id == novel.id).all()
    timeline_text = NovelEngine.format_recent_timelines(all_timelines, max_chapters=5)
    if timeline_text:
        memory_text += f"\n\n【最近重大事件时间线】\n{timeline_text}"

    chapters = db.query(Chapter).filter(Chapter.novel_id == novel.id).order_by(Chapter.chapter_num).all()
    prev_summaries = NovelEngine.get_prev_summaries(chapters, chapter_num)

    # 第1次生成
    content = await NovelEngine.write_chapter(
        chapter_num=chapter_num,
        chapter_outline=chapter_outline,
        characters=chars_text,
        memory=memory_text,
        prev_summaries=prev_summaries,
        style_guide=novel.style_guide,
    )

    # 写后审计
    audit_result = await NovelEngine.audit_chapter(
        chapter_content=content,
        chapter_num=chapter_num,
        chapter_outline=chapter_outline,
        characters=chars_text,
        memory=memory_text,
        style_guide=novel.style_guide,
        prev_summaries=prev_summaries,
    )

    rewrite_count = 0
    # 门禁：分数<70 自动重写1次
    if audit_result["score"] < 70:
        rewrite_count = 1
        content = await NovelEngine.rewrite_chapter(
            chapter_content=content,
            audit_result=audit_result,
            chapter_num=chapter_num,
            chapter_outline=chapter_outline,
            characters=chars_text,
            memory=memory_text,
            prev_summaries=prev_summaries,
            style_guide=novel.style_guide,
        )
        # 重写后重新审计
        audit_result = await NovelEngine.audit_chapter(
            chapter_content=content,
            chapter_num=chapter_num,
            chapter_outline=chapter_outline,
            characters=chars_text,
            memory=memory_text,
            style_guide=novel.style_guide,
            prev_summaries=prev_summaries,
        )

    summary = await NovelEngine.summarize_chapter(content, chapter_num)

    import json as _json
    chapter = Chapter(
        novel_id=novel.id,
        chapter_num=chapter_num,
        title=title,
        content=content,
        summary=summary,
        audit_score=audit_result["score"],
        audit_result=_json.dumps(audit_result, ensure_ascii=False),
        rewrite_count=rewrite_count,
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)

    # 按章节存储记忆
    new_memory = await NovelEngine.compress_memory(memory_text, content, chapter_num)
    memory = Memory(novel_id=novel.id, chapter_num=chapter_num, content=new_memory)
    db.add(memory)
    db.commit()

    # 伏笔追踪：扫描新伏笔 + 检查回收
    try:
        new_foreshadowings = await NovelEngine.extract_foreshadowing(content, chapter_num)
        for fs in new_foreshadowings:
            db.add(Foreshadowing(
                novel_id=novel.id,
                chapter_planted=chapter_num,
                content=fs.get("content", ""),
                priority=fs.get("priority", "medium"),
            ))
        if pending_foreshadowings:
            resolved_ids = await NovelEngine.check_foreshadowing_resolved(
                content, chapter_num,
                [{"id": f.id, "content": f.content} for f in pending_foreshadowings]
            )
            for f in pending_foreshadowings:
                if f.id in resolved_ids:
                    f.status = "resolved"
                    f.chapter_resolved = chapter_num
        db.commit()
    except Exception as e:
        logger.warning(f"伏笔追踪失败: {e}")

    # 角色状态热更新
    try:
        char_names = [c.name for c in chars]
        states = await NovelEngine.extract_character_states(content, chapter_num, char_names)
        if states:
            for c in chars:
                if c.name in states:
                    import json as _json
                    c.current_state = _json.dumps(states[c.name], ensure_ascii=False)
            db.commit()
    except Exception as e:
        logger.warning(f"角色状态更新失败: {e}")

    # 时间线事件提取
    try:
        events = await NovelEngine.extract_timeline_events(content, chapter_num)
        for evt in events:
            db.add(Timeline(
                novel_id=novel.id,
                chapter_num=chapter_num,
                event=evt.get("event", ""),
                time_label=evt.get("time_label", ""),
            ))
        db.commit()
    except Exception as e:
        logger.warning(f"时间线事件提取失败: {e}")

    return {
        "status": "success",
        "chapter": {
            "id": chapter.id,
            "chapter_num": chapter_num,
            "title": title,
            "content": content,
            "summary": summary,
            "audit_score": audit_result["score"],
            "audit_result": audit_result,
            "rewrite_count": rewrite_count,
        },
        "memory": new_memory,
    }


@router.post("/{novel_id}/chapters/stream")
async def stream_chapter(novel_id: int, req: dict,
                         user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """流式生成章节（SSE）"""
    novel = _get_owned_novel(novel_id, user, db)
    chapter_num = req.get("chapter_num", 1)
    chapter_outline = req.get("chapter_outline", "")
    title = req.get("title", f"第{chapter_num}章")

    chars = db.query(Character).filter(Character.novel_id == novel.id).all()
    chars_text = "\n".join([f"- {c.name}：{c.personality or ''}" for c in chars])

    # 注入角色当前状态
    char_states_text = NovelEngine.format_character_states(chars)
    if char_states_text:
        chars_text += f"\n\n【角色当前状态】\n{char_states_text}"

    # 获取合并记忆
    all_memories = db.query(Memory).filter(Memory.novel_id == novel.id).all()
    memory_parts = []
    for m in all_memories:
        if m.chapter_num:
            memory_parts.append(f"第{m.chapter_num}章后：{m.content}")
        else:
            memory_parts.append(f"全局：{m.content}")
    memory_text = "\n".join(memory_parts) if memory_parts else "（初始状态）"

    # 查询未回收伏笔，注入到记忆中
    pending_foreshadowings = db.query(Foreshadowing).filter(
        Foreshadowing.novel_id == novel.id, Foreshadowing.status == "pending"
    ).all()
    if pending_foreshadowings:
        foreshadow_text = NovelEngine.format_pending_foreshadowings(pending_foreshadowings)
        memory_text += f"\n\n【未回收伏笔（请注意适时回收）】\n{foreshadow_text}"

    # 查询最近时间线，注入到记忆中
    all_timelines = db.query(Timeline).filter(Timeline.novel_id == novel.id).all()
    timeline_text = NovelEngine.format_recent_timelines(all_timelines, max_chapters=5)
    if timeline_text:
        memory_text += f"\n\n【最近重大事件时间线】\n{timeline_text}"

    chapters = db.query(Chapter).filter(Chapter.novel_id == novel.id).order_by(Chapter.chapter_num).all()
    prev_summaries = NovelEngine.get_prev_summaries(chapters, chapter_num)

    content_buf = []

    async def generate():
        try:
            async for chunk in NovelEngine.write_chapter_stream(
                chapter_num=chapter_num,
                chapter_outline=chapter_outline,
                characters=chars_text,
                memory=memory_text,
                prev_summaries=prev_summaries,
                style_guide=novel.style_guide,
            ):
                content_buf.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'data': chunk}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            full_content = "".join(content_buf)
            if full_content:
                try:
                    # 写后审计
                    yield f"data: {json.dumps({'type': 'audit_start'}, ensure_ascii=False)}\n\n"
                    audit_result = await NovelEngine.audit_chapter(
                        chapter_content=full_content,
                        chapter_num=chapter_num,
                        chapter_outline=chapter_outline,
                        characters=chars_text,
                        memory=memory_text,
                        style_guide=novel.style_guide,
                        prev_summaries=prev_summaries,
                    )
                    yield f"data: {json.dumps({'type': 'audit_done', 'data': audit_result}, ensure_ascii=False)}\n\n"

                    rewrite_count = 0
                    # 门禁：分数<70 自动重写1次
                    if audit_result["score"] < 70:
                        rewrite_count = 1
                        _score = audit_result["score"]
                        yield f"data: {json.dumps({'type': 'rewrite_start', 'data': f'审计分数{_score}，正在重写...'}, ensure_ascii=False)}\n\n"
                        full_content = await NovelEngine.rewrite_chapter(
                            chapter_content=full_content,
                            audit_result=audit_result,
                            chapter_num=chapter_num,
                            chapter_outline=chapter_outline,
                            characters=chars_text,
                            memory=memory_text,
                            prev_summaries=prev_summaries,
                            style_guide=novel.style_guide,
                        )
                        # 重写后重新审计
                        audit_result = await NovelEngine.audit_chapter(
                            chapter_content=full_content,
                            chapter_num=chapter_num,
                            chapter_outline=chapter_outline,
                            characters=chars_text,
                            memory=memory_text,
                            style_guide=novel.style_guide,
                            prev_summaries=prev_summaries,
                        )
                        yield f"data: {json.dumps({'type': 'rewrite_done', 'data': {'content': full_content, 'audit': audit_result}}, ensure_ascii=False)}\n\n"

                    summary = await NovelEngine.summarize_chapter(full_content, chapter_num)
                    chapter = Chapter(
                        novel_id=novel.id,
                        chapter_num=chapter_num,
                        title=title,
                        content=full_content,
                        summary=summary,
                        audit_score=audit_result["score"],
                        audit_result=json.dumps(audit_result, ensure_ascii=False),
                        rewrite_count=rewrite_count,
                    )
                    db.add(chapter)
                    db.commit()
                    db.refresh(chapter)

                    # 按章节存储记忆
                    new_memory = await NovelEngine.compress_memory(memory_text, full_content, chapter_num)
                    memory = Memory(novel_id=novel.id, chapter_num=chapter_num, content=new_memory)
                    db.add(memory)
                    db.commit()

                    # 伏笔追踪：扫描新伏笔 + 检查回收
                    try:
                        new_fs = await NovelEngine.extract_foreshadowing(full_content, chapter_num)
                        for fs in new_fs:
                            db.add(Foreshadowing(
                                novel_id=novel.id,
                                chapter_planted=chapter_num,
                                content=fs.get("content", ""),
                                priority=fs.get("priority", "medium"),
                            ))
                        if pending_foreshadowings:
                            resolved_ids = await NovelEngine.check_foreshadowing_resolved(
                                full_content, chapter_num,
                                [{"id": f.id, "content": f.content} for f in pending_foreshadowings]
                            )
                            for f in pending_foreshadowings:
                                if f.id in resolved_ids:
                                    f.status = "resolved"
                                    f.chapter_resolved = chapter_num
                        db.commit()
                    except Exception as e:
                        logger.warning(f"伏笔追踪失败: {e}")

                    # 角色状态热更新
                    try:
                        char_names = [c.name for c in chars]
                        states = await NovelEngine.extract_character_states(full_content, chapter_num, char_names)
                        if states:
                            for c in chars:
                                if c.name in states:
                                    import json as _json
                                    c.current_state = _json.dumps(states[c.name], ensure_ascii=False)
                            db.commit()
                    except Exception as e:
                        logger.warning(f"角色状态更新失败: {e}")

                    # 时间线事件提取
                    try:
                        events = await NovelEngine.extract_timeline_events(full_content, chapter_num)
                        for evt in events:
                            db.add(Timeline(
                                novel_id=novel.id,
                                chapter_num=chapter_num,
                                event=evt.get("event", ""),
                                time_label=evt.get("time_label", ""),
                            ))
                        db.commit()
                    except Exception as e:
                        logger.warning(f"时间线事件提取失败: {e}")

                    yield f"data: {json.dumps({'type': 'done', 'data': {'chapter_id': chapter.id, 'summary': summary, 'memory': new_memory, 'audit_score': audit_result['score'], 'audit_result': audit_result, 'rewrite_count': rewrite_count}}, ensure_ascii=False)}\n\n"
                except Exception as e:
                    logger.error(f"保存章节失败: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'data': f'保存失败: {str(e)}'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/{novel_id}/chapters")
def list_chapters(novel_id: int, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """获取章节列表"""
    novel = _get_owned_novel(novel_id, user, db)
    return _orm_list(
        db.query(Chapter)
        .filter(Chapter.novel_id == novel.id)
        .order_by(Chapter.chapter_num)
        .all()
    )


@router.get("/{novel_id}/chapters/{chapter_id}")
def get_chapter(novel_id: int, chapter_id: int, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """获取单个章节"""
    novel = _get_owned_novel(novel_id, user, db)
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id, Chapter.novel_id == novel.id).first()
    if chapter is None:
        raise HTTPException(status_code=404, detail="章节不存在")
    return chapter


@router.put("/{novel_id}/chapters/{chapter_id}")
def update_chapter(novel_id: int, chapter_id: int, req: dict,
                   user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """更新章节内容"""
    novel = _get_owned_novel(novel_id, user, db)
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id, Chapter.novel_id == novel.id).first()
    if chapter is None:
        raise HTTPException(status_code=404, detail="章节不存在")
    if "content" in req:
        chapter.content = req["content"]
    if "title" in req:
        chapter.title = req["title"]
    if "summary" in req:
        chapter.summary = req["summary"]
    db.commit()
    db.refresh(chapter)
    return chapter


@router.delete("/{novel_id}/chapters/{chapter_id}")
def delete_chapter(novel_id: int, chapter_id: int, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """删除章节"""
    novel = _get_owned_novel(novel_id, user, db)
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id, Chapter.novel_id == novel.id).first()
    if chapter is None:
        raise HTTPException(status_code=404, detail="章节不存在")
    db.delete(chapter)
    db.commit()
    return {"status": "success", "message": "章节已删除"}


# ============ 记忆管理（分章节） ============

@router.get("/{novel_id}/memory")
def get_memory(novel_id: int, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    """获取小说记忆（分章节返回）"""
    novel = _get_owned_novel(novel_id, user, db)
    memories = (
        db.query(Memory)
        .filter(Memory.novel_id == novel.id)
        .order_by(Memory.chapter_num.is_(None), Memory.chapter_num.asc())
        .all()
    )
    if not memories:
        return {"chapters": [], "global": ""}
    chapters_mem = [{"id": m.id, "chapter_num": m.chapter_num, "content": m.content} for m in memories if m.chapter_num]
    global_mem = next((m.content for m in memories if not m.chapter_num), "")
    return {"chapters": chapters_mem, "global": global_mem}


@router.put("/{novel_id}/memory")
def update_memory(novel_id: int, req: dict, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """更新记忆（支持按章节更新和全局更新）"""
    novel = _get_owned_novel(novel_id, user, db)

    # 更新全局记忆
    if "global" in req:
        global_mem = db.query(Memory).filter(
            Memory.novel_id == novel.id, Memory.chapter_num.is_(None)
        ).first()
        if global_mem:
            global_mem.content = req["global"]
        else:
            db.add(Memory(novel_id=novel.id, chapter_num=None, content=req["global"]))

    # 更新某章记忆
    if "chapter_num" in req and "content" in req:
        ch_num = req["chapter_num"]
        mem = db.query(Memory).filter(
            Memory.novel_id == novel.id, Memory.chapter_num == ch_num
        ).first()
        if mem:
            mem.content = req["content"]
        else:
            db.add(Memory(novel_id=novel.id, chapter_num=ch_num, content=req["content"]))

    # 批量更新
    if "chapters" in req:
        for item in req["chapters"]:
            ch_num = item.get("chapter_num")
            content = item.get("content", "")
            mem = db.query(Memory).filter(
                Memory.novel_id == novel.id, Memory.chapter_num == ch_num
            ).first()
            if mem:
                mem.content = content
            else:
                db.add(Memory(novel_id=novel.id, chapter_num=ch_num, content=content))

    db.commit()
    return {"status": "success"}


@router.delete("/{novel_id}/memory/{memory_id}")
def delete_memory(novel_id: int, memory_id: int, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """删除单条记忆"""
    novel = _get_owned_novel(novel_id, user, db)
    mem = db.query(Memory).filter(Memory.id == memory_id, Memory.novel_id == novel.id).first()
    if mem is None:
        raise HTTPException(status_code=404, detail="记忆不存在")
    db.delete(mem)
    db.commit()
    return {"status": "success"}


# ============ 续写：导入TXT ============

@router.post("/{novel_id}/import")
async def import_novel_text(
    novel_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """导入已有小说TXT，AI自动拆分章节、提取角色、生成大纲"""
    novel = _get_owned_novel(novel_id, user, db)

    content = await file.read()
    # 尝试多种编码
    text = None
    for enc in ["utf-8", "gbk", "gb2312", "utf-16"]:
        try:
            text = content.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    if text is None:
        raise HTTPException(status_code=400, detail="无法识别文件编码，请保存为UTF-8格式")

    # AI解析
    try:
        result = await NovelEngine.parse_imported_novel(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI解析失败: {str(e)}")

    # 保存章节（所有章节都生成临时记忆，保证续写时有上下文；AI记忆可后续手动触发生成）
    for ch in result["chapters"]:
        # 临时摘要：内容前50字
        summary = (ch["content"][:50] + "...") if len(ch["content"]) > 50 else ch["content"]
        # 临时记忆：内容前150字（作为续写上下文，用户可在记忆Tab点击"AI重新生成"替换为结构化记忆）
        temp_memory = f"【第{ch['chapter_num']}章·临时记忆】\n{ch['content'][:150]}"
        chapter = Chapter(
            novel_id=novel.id,
            chapter_num=ch["chapter_num"],
            title=ch["title"],
            content=ch["content"],
            summary=summary,
        )
        db.add(chapter)
        db.add(Memory(novel_id=novel.id, chapter_num=ch["chapter_num"], content=temp_memory))

    # 保存提取的角色
    for c in result["characters"]:
        db.add(Character(
            novel_id=novel.id,
            name=c.get("name", ""),
            personality=c.get("personality", ""),
            background=c.get("background", ""),
        ))

    # 更新大纲和简介（outline可能是列表，转成字符串）
    if result["outline"]:
        outline_val = result["outline"]
        if isinstance(outline_val, list):
            outline_val = "\n".join(str(item) for item in outline_val)
        novel.outline = str(outline_val)
    if result["description"] and not novel.description:
        novel.description = str(result["description"])
    if result["genre"] and not novel.genre:
        novel.genre = str(result["genre"])

    # 保存全局记忆（chapter_num为NULL）
    if result.get("global_memory"):
        db.add(Memory(novel_id=novel.id, chapter_num=None, content=result["global_memory"]))

    db.commit()

    return {
        "status": "success",
        "chapters_imported": len(result["chapters"]),
        "characters_extracted": len(result["characters"]),
        "outline": novel.outline,
        "description": novel.description,
        "genre": novel.genre,
    }


# ============ AI扫描补充角色 ============

@router.post("/{novel_id}/extract-characters")
async def extract_characters(
    novel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """AI扫描所有章节，补充提取中后期出现的角色"""
    novel = _get_owned_novel(novel_id, user, db)
    chapters = db.query(Chapter).filter(Chapter.novel_id == novel.id).order_by(Chapter.chapter_num.asc()).all()
    if not chapters:
        raise HTTPException(status_code=404, detail="没有章节可扫描")

    # 已有角色名集合
    existing_names = {c.name for c in db.query(Character).filter(Character.novel_id == novel.id).all()}

    try:
        new_chars = await NovelEngine.extract_characters_from_chapters(chapters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI扫描失败: {str(e)}")

    # 只添加新角色
    added = []
    for c in new_chars:
        name = c.get("name", "").strip()
        if name and name not in existing_names:
            db.add(Character(
                novel_id=novel.id,
                name=name,
                personality=c.get("personality", ""),
                background=c.get("background", ""),
            ))
            existing_names.add(name)
            added.append(name)

    db.commit()
    return {"status": "success", "added": added, "total_added": len(added)}


# ============ AI根据已有章节重新生成大纲 ============

@router.post("/{novel_id}/regenerate-outline")
async def regenerate_outline(
    novel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """根据已有章节内容重新生成完整大纲"""
    novel = _get_owned_novel(novel_id, user, db)
    chapters = db.query(Chapter).filter(Chapter.novel_id == novel.id).order_by(Chapter.chapter_num.asc()).all()
    if not chapters:
        raise HTTPException(status_code=404, detail="没有章节可分析")

    try:
        outline = await NovelEngine.generate_outline_from_chapters(chapters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"大纲生成失败: {str(e)}")

    novel.outline = outline
    db.commit()
    return {"status": "success", "outline": outline}


# ============ AI生成全局记忆 ============

@router.post("/{novel_id}/generate-global-memory")
async def generate_global_memory(
    novel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """根据所有章节内容生成全局记忆"""
    novel = _get_owned_novel(novel_id, user, db)
    chapters = db.query(Chapter).filter(Chapter.novel_id == novel.id).order_by(Chapter.chapter_num.asc()).all()
    if not chapters:
        raise HTTPException(status_code=404, detail="没有章节可分析")

    try:
        # 转成dict列表格式（兼容方法签名）
        ch_data = [{"chapter_num": c.chapter_num, "title": c.title, "content": c.content} for c in chapters]
        global_mem = await NovelEngine.generate_global_memory_from_chapters(ch_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"全局记忆生成失败: {str(e)}")

    # 更新或创建全局记忆（chapter_num为NULL）
    mem = db.query(Memory).filter(
        Memory.novel_id == novel.id,
        Memory.chapter_num.is_(None),
    ).first()
    if mem:
        mem.content = global_mem
    else:
        db.add(Memory(novel_id=novel.id, chapter_num=None, content=global_mem))

    db.commit()
    return {"status": "success", "global_memory": global_mem}


# ============ AI重新生成记忆 ============

@router.post("/{novel_id}/regenerate-memory")
async def regenerate_memory(
    novel_id: int,
    payload: dict = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """对指定章节（或全部章节）调用AI重新生成结构化记忆。
    payload: {"chapter_nums": [1,2,3]} 为空则全部章节"""
    novel = _get_owned_novel(novel_id, user, db)
    target_nums = (payload or {}).get("chapter_nums") or []

    query = db.query(Chapter).filter(Chapter.novel_id == novel.id)
    if target_nums:
        query = query.filter(Chapter.chapter_num.in_(target_nums))
    chapters = query.order_by(Chapter.chapter_num.asc()).all()

    if not chapters:
        raise HTTPException(status_code=404, detail="没有可处理的章节")

    results = []
    for ch in chapters:
        try:
            memory_content = await NovelEngine.generate_memory_for_chapter(ch.content, ch.chapter_num)
            # 更新或创建记忆
            mem = db.query(Memory).filter(
                Memory.novel_id == novel.id,
                Memory.chapter_num == ch.chapter_num,
            ).first()
            if mem:
                mem.content = memory_content
            else:
                db.add(Memory(novel_id=novel.id, chapter_num=ch.chapter_num, content=memory_content))
            results.append({"chapter_num": ch.chapter_num, "status": "ok"})
        except Exception as e:
            results.append({"chapter_num": ch.chapter_num, "status": "failed", "error": str(e)})

    db.commit()
    return {"status": "success", "results": results, "total": len(results)}


# ============ AI修改意见 ============

@router.post("/{novel_id}/review")
async def review_chapters(
    novel_id: int,
    req: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """AI扫描选中章节，提出修改建议（不改写）"""
    novel = _get_owned_novel(novel_id, user, db)

    chapter_ids = req.get("chapter_ids", [])
    if not chapter_ids:
        raise HTTPException(status_code=400, detail="请至少选择一个章节")

    chapters = (
        db.query(Chapter)
        .filter(Chapter.novel_id == novel.id, Chapter.id.in_(chapter_ids))
        .order_by(Chapter.chapter_num)
        .all()
    )

    if not chapters:
        raise HTTPException(status_code=404, detail="未找到选中章节")

    chapters_data = [{"chapter_num": c.chapter_num, "title": c.title or f"第{c.chapter_num}章", "content": c.content} for c in chapters]

    # 拼接角色设定
    chars = db.query(Character).filter(Character.novel_id == novel.id).all()
    characters_str = "\n".join([f"- {c.name}：{c.personality}（{c.background}）" for c in chars]) if chars else ""

    # 拼接记忆（全局 + 选中章节之前的最近几章记忆）
    mems = (
        db.query(Memory)
        .filter(Memory.novel_id == novel.id)
        .order_by(Memory.chapter_num.is_(None), Memory.chapter_num.asc())
        .all()
    )
    memory_parts = []
    for m in mems:
        if m.chapter_num is None:
            memory_parts.append(f"[全局] {m.content}")
        else:
            memory_parts.append(f"[第{m.chapter_num}章后] {m.content}")
    memory_str = "\n".join(memory_parts) if memory_parts else ""

    try:
        suggestions = await NovelEngine.review_chapters(
            chapters_data,
            characters=characters_str,
            memory=memory_str,
            style_guide=novel.style_guide or "",
            outline=novel.outline or "",
        )
        return {"status": "success", "suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI审阅失败: {str(e)}")


# ============ 伏笔管理 ============

@router.get("/{novel_id}/foreshadowings")
def list_foreshadowings(novel_id: int, user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """获取伏笔列表（按状态和埋设章节排序）"""
    novel = _get_owned_novel(novel_id, user, db)
    return _orm_list(
        db.query(Foreshadowing)
        .filter(Foreshadowing.novel_id == novel.id)
        .order_by(Foreshadowing.status, Foreshadowing.chapter_planted)
        .all()
    )


@router.post("/{novel_id}/foreshadowings", status_code=status.HTTP_201_CREATED)
def create_foreshadowing(novel_id: int, req: dict,
                         user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """手动添加伏笔"""
    novel = _get_owned_novel(novel_id, user, db)
    fs = Foreshadowing(
        novel_id=novel.id,
        chapter_planted=req.get("chapter_planted", 1),
        content=req.get("content", ""),
        priority=req.get("priority", "medium"),
    )
    db.add(fs)
    db.commit()
    db.refresh(fs)
    return fs


@router.put("/{novel_id}/foreshadowings/{fs_id}")
def update_foreshadowing(novel_id: int, fs_id: int, req: dict,
                         user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """更新伏笔（可修改状态、内容、优先级）"""
    novel = _get_owned_novel(novel_id, user, db)
    fs = db.query(Foreshadowing).filter(Foreshadowing.id == fs_id, Foreshadowing.novel_id == novel.id).first()
    if fs is None:
        raise HTTPException(status_code=404, detail="伏笔不存在")
    if "content" in req:
        fs.content = req["content"]
    if "priority" in req:
        fs.priority = req["priority"]
    if "status" in req:
        fs.status = req["status"]
    if "chapter_resolved" in req:
        fs.chapter_resolved = req["chapter_resolved"]
    db.commit()
    db.refresh(fs)
    return fs


@router.delete("/{novel_id}/foreshadowings/{fs_id}")
def delete_foreshadowing(novel_id: int, fs_id: int,
                         user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """删除伏笔"""
    novel = _get_owned_novel(novel_id, user, db)
    fs = db.query(Foreshadowing).filter(Foreshadowing.id == fs_id, Foreshadowing.novel_id == novel.id).first()
    if fs is None:
        raise HTTPException(status_code=404, detail="伏笔不存在")
    db.delete(fs)
    db.commit()
    return {"status": "success"}


@router.post("/{novel_id}/foreshadowings/batch-delete")
def batch_delete_foreshadowings(novel_id: int, req: dict,
                                user: User = Depends(get_current_user),
                                db: Session = Depends(get_db)):
    """批量删除伏笔"""
    novel = _get_owned_novel(novel_id, user, db)
    ids = req.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="请选择要删除的伏笔")
    count = db.query(Foreshadowing).filter(
        Foreshadowing.id.in_(ids), Foreshadowing.novel_id == novel.id
    ).delete(synchronize_session=False)
    db.commit()
    return {"status": "success", "deleted": count}


@router.post("/{novel_id}/foreshadowings/batch-update")
def batch_update_foreshadowings(novel_id: int, req: dict,
                                user: User = Depends(get_current_user),
                                db: Session = Depends(get_db)):
    """批量更新伏笔（如标记回收）"""
    novel = _get_owned_novel(novel_id, user, db)
    ids = req.get("ids", [])
    data = req.get("data", {})
    if not ids:
        raise HTTPException(status_code=400, detail="请选择要更新的伏笔")
    count = db.query(Foreshadowing).filter(
        Foreshadowing.id.in_(ids), Foreshadowing.novel_id == novel.id
    ).update(data, synchronize_session=False)
    db.commit()
    return {"status": "success", "updated": count}


@router.post("/{novel_id}/foreshadowings/scan")
async def scan_foreshadowings(novel_id: int, req: dict,
                              user: User = Depends(get_current_user),
                              db: Session = Depends(get_db)):
    """手动扫描指定章节的伏笔（提取新伏笔 + 检查回收）"""
    novel = _get_owned_novel(novel_id, user, db)
    chapter_ids = req.get("chapter_ids", [])
    if not chapter_ids:
        raise HTTPException(status_code=400, detail="请至少选择一个章节")

    chapters = (
        db.query(Chapter)
        .filter(Chapter.novel_id == novel.id, Chapter.id.in_(chapter_ids))
        .order_by(Chapter.chapter_num)
        .all()
    )

    pending = db.query(Foreshadowing).filter(
        Foreshadowing.novel_id == novel.id, Foreshadowing.status == "pending"
    ).all()

    new_count = 0
    resolved_count = 0
    for ch in chapters:
        try:
            new_fs = await NovelEngine.extract_foreshadowing(ch.content, ch.chapter_num)
            for fs in new_fs:
                db.add(Foreshadowing(
                    novel_id=novel.id,
                    chapter_planted=ch.chapter_num,
                    content=fs.get("content", ""),
                    priority=fs.get("priority", "medium"),
                ))
                new_count += 1
            if pending:
                resolved_ids = await NovelEngine.check_foreshadowing_resolved(
                    ch.content, ch.chapter_num,
                    [{"id": f.id, "content": f.content} for f in pending]
                )
                for f in pending:
                    if f.id in resolved_ids:
                        f.status = "resolved"
                        f.chapter_resolved = ch.chapter_num
                        resolved_count += 1
        except Exception as e:
            logger.warning(f"扫描第{ch.chapter_num}章伏笔失败: {e}")

    db.commit()
    return {"status": "success", "new_count": new_count, "resolved_count": resolved_count}


# ============ 时间线管理 ============

@router.get("/{novel_id}/timelines")
def list_timelines(novel_id: int, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """获取时间线列表"""
    novel = _get_owned_novel(novel_id, user, db)
    return _orm_list(
        db.query(Timeline)
        .filter(Timeline.novel_id == novel.id)
        .order_by(Timeline.chapter_num, Timeline.id)
        .all()
    )


@router.post("/{novel_id}/timelines", status_code=status.HTTP_201_CREATED)
def create_timeline(novel_id: int, req: dict,
                    user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """手动添加时间线事件"""
    novel = _get_owned_novel(novel_id, user, db)
    tl = Timeline(
        novel_id=novel.id,
        chapter_num=req.get("chapter_num", 1),
        event=req.get("event", ""),
        time_label=req.get("time_label", ""),
    )
    db.add(tl)
    db.commit()
    db.refresh(tl)
    return tl


@router.put("/{novel_id}/timelines/{tl_id}")
def update_timeline(novel_id: int, tl_id: int, req: dict,
                    user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """更新时间线事件"""
    novel = _get_owned_novel(novel_id, user, db)
    tl = db.query(Timeline).filter(Timeline.id == tl_id, Timeline.novel_id == novel.id).first()
    if tl is None:
        raise HTTPException(status_code=404, detail="时间线事件不存在")
    if "event" in req:
        tl.event = req["event"]
    if "time_label" in req:
        tl.time_label = req["time_label"]
    if "chapter_num" in req:
        tl.chapter_num = req["chapter_num"]
    db.commit()
    db.refresh(tl)
    return tl


@router.delete("/{novel_id}/timelines/{tl_id}")
def delete_timeline(novel_id: int, tl_id: int,
                    user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """删除时间线事件"""
    novel = _get_owned_novel(novel_id, user, db)
    tl = db.query(Timeline).filter(Timeline.id == tl_id, Timeline.novel_id == novel.id).first()
    if tl is None:
        raise HTTPException(status_code=404, detail="时间线事件不存在")
    db.delete(tl)
    db.commit()
    return {"status": "success"}


@router.post("/{novel_id}/timelines/batch-delete")
def batch_delete_timelines(novel_id: int, req: dict,
                           user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    """批量删除时间线事件"""
    novel = _get_owned_novel(novel_id, user, db)
    ids = req.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="请选择要删除的事件")
    count = db.query(Timeline).filter(
        Timeline.id.in_(ids), Timeline.novel_id == novel.id
    ).delete(synchronize_session=False)
    db.commit()
    return {"status": "success", "deleted": count}


@router.post("/{novel_id}/timelines/scan")
async def scan_timelines(novel_id: int, req: dict,
                         user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """手动扫描指定章节的时间线事件"""
    novel = _get_owned_novel(novel_id, user, db)
    chapter_ids = req.get("chapter_ids", [])
    if not chapter_ids:
        raise HTTPException(status_code=400, detail="请至少选择一个章节")

    chapters = (
        db.query(Chapter)
        .filter(Chapter.novel_id == novel.id, Chapter.id.in_(chapter_ids))
        .order_by(Chapter.chapter_num)
        .all()
    )

    new_count = 0
    for ch in chapters:
        try:
            events = await NovelEngine.extract_timeline_events(ch.content, ch.chapter_num)
            for evt in events:
                db.add(Timeline(
                    novel_id=novel.id,
                    chapter_num=ch.chapter_num,
                    event=evt.get("event", ""),
                    time_label=evt.get("time_label", ""),
                ))
                new_count += 1
        except Exception as e:
            logger.warning(f"扫描第{ch.chapter_num}章时间线失败: {e}")

    db.commit()
    return {"status": "success", "new_count": new_count}

# ============ 文风分析 ============

@router.post("/{novel_id}/style/analyze")
async def analyze_style(
    novel_id: int,
    req: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """分析参考文本的文风，将结果写入小说style_guide"""
    novel = db.query(Novel).filter(Novel.id == novel_id, Novel.user_id == user.id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    reference_text = req.get("reference_text", "")
    if len(reference_text) < 500:
        raise HTTPException(status_code=400, detail="参考文本至少500字")

    style_data = await NovelEngine.analyze_style(reference_text)
    style_guide = NovelEngine.format_style_guide(style_data)

    novel.style_guide = style_guide
    novel.style_data = json.dumps(style_data, ensure_ascii=False)
    db.commit()

    return {"status": "success", "style_guide": style_guide, "style_data": style_data}


# ============ 版本归档 ============

@router.get("/{novel_id}/versions")
def list_versions(novel_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取小说版本列表"""
    novel = db.query(Novel).filter(Novel.id == novel_id, Novel.user_id == user.id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    versions = db.query(Version).filter(Version.novel_id == novel_id).order_by(Version.created_at.desc()).all()
    return [{"id": v.id, "version_name": v.version_name, "change_summary": v.change_summary,
             "created_at": v.created_at.isoformat() if v.created_at else None} for v in versions]


@router.post("/{novel_id}/versions")
def create_version(novel_id: int, req: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """创建版本快照"""
    novel = db.query(Novel).filter(Novel.id == novel_id, Novel.user_id == user.id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    # 构建快照
    chapters = db.query(Chapter).filter(Chapter.novel_id == novel_id).order_by(Chapter.chapter_num).all()
    snapshot = {
        "title": novel.title,
        "genre": novel.genre,
        "description": novel.description,
        "outline": novel.outline,
        "style_guide": novel.style_guide,
        "chapters": [{"chapter_num": c.chapter_num, "title": c.title, "content": c.content, "summary": c.summary}
                      for c in chapters],
    }

    version = Version(
        novel_id=novel_id,
        version_name=req.get("version_name", f"v{datetime.now().strftime('%Y%m%d%H%M%S')}"),
        snapshot=json.dumps(snapshot, ensure_ascii=False),
        change_summary=req.get("change_summary", ""),
    )
    db.add(version)
    db.commit()
    return {"status": "success", "version_id": version.id, "version_name": version.version_name}


@router.get("/{novel_id}/versions/{version_id}")
def get_version(novel_id: int, version_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取版本详情（含快照）"""
    novel = db.query(Novel).filter(Novel.id == novel_id, Novel.user_id == user.id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    version = db.query(Version).filter(Version.id == version_id, Version.novel_id == novel_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    return {"id": version.id, "version_name": version.version_name,
            "change_summary": version.change_summary,
            "created_at": version.created_at.isoformat() if version.created_at else None,
            "snapshot": json.loads(version.snapshot) if version.snapshot else None}


@router.post("/{novel_id}/versions/{version_id}/restore")
def restore_version(novel_id: int, version_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """恢复到指定版本"""
    novel = db.query(Novel).filter(Novel.id == novel_id, Novel.user_id == user.id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    version = db.query(Version).filter(Version.id == version_id, Version.novel_id == novel_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    # 先创建当前状态的快照
    current_chapters = db.query(Chapter).filter(Chapter.novel_id == novel_id).order_by(Chapter.chapter_num).all()
    current_snapshot = {
        "title": novel.title, "genre": novel.genre, "description": novel.description,
        "outline": novel.outline, "style_guide": novel.style_guide,
        "chapters": [{"chapter_num": c.chapter_num, "title": c.title, "content": c.content, "summary": c.summary}
                      for c in current_chapters],
    }
    backup = Version(
        novel_id=novel_id,
        version_name=f"恢复前备份_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        snapshot=json.dumps(current_snapshot, ensure_ascii=False),
        change_summary=f"恢复到版本{version.version_name}前的自动备份",
    )
    db.add(backup)

    # 恢复快照
    snapshot = json.loads(version.snapshot)
    novel.title = snapshot.get("title", novel.title)
    novel.genre = snapshot.get("genre", novel.genre)
    novel.description = snapshot.get("description", novel.description)
    novel.outline = snapshot.get("outline", novel.outline)
    novel.style_guide = snapshot.get("style_guide", novel.style_guide)

    # 恢复章节
    db.query(Chapter).filter(Chapter.novel_id == novel_id).delete()
    for ch_data in snapshot.get("chapters", []):
        db.add(Chapter(
            novel_id=novel_id,
            chapter_num=ch_data["chapter_num"],
            title=ch_data.get("title", ""),
            content=ch_data.get("content", ""),
            summary=ch_data.get("summary", ""),
        ))

    db.commit()
    return {"status": "success", "message": f"已恢复到版本 {version.version_name}", "backup_version_id": backup.id}


@router.delete("/{novel_id}/versions/{version_id}")
def delete_version(novel_id: int, version_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """删除版本"""
    novel = db.query(Novel).filter(Novel.id == novel_id, Novel.user_id == user.id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    version = db.query(Version).filter(Version.id == version_id, Version.novel_id == novel_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    db.delete(version)
    db.commit()
    return {"status": "success", "message": "版本已删除"}


# ============ 分卷规划 + 情绪曲线 ============

@router.post("/{novel_id}/volumes/plan")
async def plan_volumes(novel_id: int, req: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """AI生成分卷规划"""
    novel = db.query(Novel).filter(Novel.id == novel_id, Novel.user_id == user.id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    total_chapters = req.get("total_chapters", 100)
    num_volumes = req.get("num_volumes", 3)

    volumes = await NovelEngine.plan_volumes(
        novel.title, novel.genre or "", novel.description or "", total_chapters, num_volumes
    )
    if not volumes:
        raise HTTPException(status_code=500, detail="分卷规划生成失败")

    # 保存到小说的outline字段末尾
    volume_text = NovelEngine.format_volume_plan(volumes)
    novel.volume_plan = json.dumps(volumes, ensure_ascii=False)
    db.commit()

    return {"volumes": volumes, "volume_text": volume_text}


@router.get("/{novel_id}/volumes")
def get_volume_plan(novel_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取分卷规划"""
    novel = db.query(Novel).filter(Novel.id == novel_id, Novel.user_id == user.id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    if not novel.volume_plan:
        return {"volumes": []}
    return {"volumes": json.loads(novel.volume_plan)}


@router.post("/{novel_id}/emotion-curve")
async def analyze_emotion_curve(novel_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """分析章节情绪曲线"""
    novel = db.query(Novel).filter(Novel.id == novel_id, Novel.user_id == user.id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")

    chapters = db.query(Chapter).filter(Chapter.novel_id == novel_id).order_by(Chapter.chapter_num).all()
    if not chapters:
        raise HTTPException(status_code=400, detail="暂无章节数据")

    curve = await NovelEngine.analyze_emotion_curve(chapters)
    return {"curve": curve}
