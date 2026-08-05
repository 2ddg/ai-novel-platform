"""小说写作路由：项目管理 / 角色 / 大纲 / 章节 / 记忆 / 导入 / 审阅"""
import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_user
from models.user import User
from models.novel import Novel, Character, Chapter, Memory
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
    return db.query(Character).filter(Character.novel_id == novel.id).all()


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
    """生成单个章节（非流式）"""
    novel = _get_owned_novel(novel_id, user, db)
    chapter_num = req.get("chapter_num", 1)
    chapter_outline = req.get("chapter_outline", "")
    title = req.get("title", f"第{chapter_num}章")

    chars = db.query(Character).filter(Character.novel_id == novel.id).all()
    chars_text = "\n".join([f"- {c.name}：{c.personality or ''}" for c in chars])

    # 获取合并记忆：所有章节记忆 + 全局记忆
    all_memories = db.query(Memory).filter(Memory.novel_id == novel.id).all()
    memory_parts = []
    for m in all_memories:
        if m.chapter_num:
            memory_parts.append(f"第{m.chapter_num}章后：{m.content}")
        else:
            memory_parts.append(f"全局：{m.content}")
    memory_text = "\n".join(memory_parts) if memory_parts else "（初始状态）"

    chapters = db.query(Chapter).filter(Chapter.novel_id == novel.id).order_by(Chapter.chapter_num).all()
    prev_summaries = NovelEngine.get_prev_summaries(chapters, chapter_num)

    content = await NovelEngine.write_chapter(
        chapter_num=chapter_num,
        chapter_outline=chapter_outline,
        characters=chars_text,
        memory=memory_text,
        prev_summaries=prev_summaries,
        style_guide=novel.style_guide,
    )

    summary = await NovelEngine.summarize_chapter(content, chapter_num)

    chapter = Chapter(
        novel_id=novel.id,
        chapter_num=chapter_num,
        title=title,
        content=content,
        summary=summary,
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)

    # 按章节存储记忆
    new_memory = await NovelEngine.compress_memory(memory_text, content, chapter_num)
    memory = Memory(novel_id=novel.id, chapter_num=chapter_num, content=new_memory)
    db.add(memory)
    db.commit()

    return {
        "status": "success",
        "chapter": {
            "id": chapter.id,
            "chapter_num": chapter_num,
            "title": title,
            "content": content,
            "summary": summary,
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

    # 获取合并记忆
    all_memories = db.query(Memory).filter(Memory.novel_id == novel.id).all()
    memory_parts = []
    for m in all_memories:
        if m.chapter_num:
            memory_parts.append(f"第{m.chapter_num}章后：{m.content}")
        else:
            memory_parts.append(f"全局：{m.content}")
    memory_text = "\n".join(memory_parts) if memory_parts else "（初始状态）"

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
                    summary = await NovelEngine.summarize_chapter(full_content, chapter_num)
                    chapter = Chapter(
                        novel_id=novel.id,
                        chapter_num=chapter_num,
                        title=title,
                        content=full_content,
                        summary=summary,
                    )
                    db.add(chapter)
                    db.commit()
                    db.refresh(chapter)

                    # 按章节存储记忆
                    new_memory = await NovelEngine.compress_memory(memory_text, full_content, chapter_num)
                    memory = Memory(novel_id=novel.id, chapter_num=chapter_num, content=new_memory)
                    db.add(memory)
                    db.commit()

                    yield f"data: {json.dumps({'type': 'done', 'data': {'chapter_id': chapter.id, 'summary': summary, 'memory': new_memory}}, ensure_ascii=False)}\n\n"
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
    return (
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
