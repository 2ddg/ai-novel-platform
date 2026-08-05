"""小说写作相关表 ORM 模型"""
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Column
from sqlalchemy.orm import relationship

from database import Base


class Novel(Base):
    __tablename__ = "novels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    genre = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    outline = Column(Text, nullable=True)
    style_guide = Column(Text, nullable=True)
    style_data = Column(Text, nullable=True)
    volume_plan = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    characters = relationship("Character", back_populates="novel", cascade="all, delete-orphan")
    chapters = relationship("Chapter", back_populates="novel", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="novel", cascade="all, delete-orphan")
    foreshadowings = relationship("Foreshadowing", back_populates="novel", cascade="all, delete-orphan")
    timelines = relationship("Timeline", back_populates="novel", cascade="all, delete-orphan")
    versions = relationship("Version", back_populates="novel", cascade="all, delete-orphan")


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    personality = Column(Text, nullable=True)
    background = Column(Text, nullable=True)
    current_state = Column(Text, nullable=True)  # JSON：位置/实力/心情/持有物品/已知信息
    created_at = Column(DateTime, default=datetime.utcnow)

    novel = relationship("Novel", back_populates="characters")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    chapter_num = Column(Integer, nullable=False)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    # 写后审计：分数（0-100）+ 审阅结果（JSON字符串）+ 重写次数
    audit_score = Column(Integer, nullable=True)
    audit_result = Column(Text, nullable=True)
    rewrite_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    novel = relationship("Novel", back_populates="chapters")


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    chapter_num = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    novel = relationship("Novel", back_populates="memories")


class Foreshadowing(Base):
    """伏笔追踪表"""
    __tablename__ = "foreshadowings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    chapter_planted = Column(Integer, nullable=False)  # 埋设章节号
    content = Column(Text, nullable=False)              # 伏笔内容描述
    status = Column(String(20), default="pending")     # pending/resolved/abandoned
    chapter_resolved = Column(Integer, nullable=True)   # 回收章节号
    priority = Column(String(10), default="medium")    # high/medium/low
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    novel = relationship("Novel", back_populates="foreshadowings")


class Timeline(Base):
    """时间线：每章重大事件"""
    __tablename__ = "timelines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    chapter_num = Column(Integer, nullable=False)
    event = Column(Text, nullable=False)               # 事件描述
    time_label = Column(String(100), nullable=True)    # 时间标记（如"第三天"、"正月十五"）
    created_at = Column(DateTime, default=datetime.utcnow)

    novel = relationship("Novel", back_populates="timelines")


class Version(Base):
    """版本归档 - 小说的历史版本快照"""
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    version_name = Column(String(200), nullable=False)
    snapshot = Column(Text, nullable=False)          # JSON：小说数据快照
    change_summary = Column(Text, nullable=True)     # 变更说明
    created_at = Column(DateTime, default=datetime.utcnow)

    novel = relationship("Novel", back_populates="versions")
