"""MySQL 数据库连接（SQLAlchemy 2.0）

启动时自动创建数据库（若不存在）和所有数据表。
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from config import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE,
    DATABASE_URL,
)

logger = logging.getLogger(__name__)

# 全局 ORM 基类
Base = declarative_base()

# 默认连接（指定数据库）的引擎与会话工厂
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # 连接前检查有效性，避免 MySQL 8 断连
    pool_recycle=3600,    # 1小时回收
    echo=False,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def create_database_if_not_exists():
    """连接 MySQL 服务器（不指定库），若目标库不存在则创建。"""
    server_url = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/?charset=utf8mb4"
    )
    tmp_engine = create_engine(server_url)
    try:
        with tmp_engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
                    f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
            conn.commit()
        logger.info(f"数据库 '{MYSQL_DATABASE}' 已就绪")
    except Exception as e:
        logger.error(f"创建数据库失败：{e}")
        raise
    finally:
        tmp_engine.dispose()


def init_db():
    """创建数据库 + 所有数据表（启动时调用一次）"""
    create_database_if_not_exists()
    # 导入模型以确保它们被注册到 Base.metadata
    from models import user, knowledge, chat, novel  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # 轻量级迁移：为已有的 memories 表添加 chapter_num 列（MySQL兼容写法）
    try:
        with engine.connect() as conn:
            # 先检查列是否存在
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = :db AND table_name = 'memories' AND column_name = 'chapter_num'"
            ), {"db": MYSQL_DATABASE})
            if result.scalar() == 0:
                conn.execute(text("ALTER TABLE memories ADD COLUMN chapter_num INT NULL"))
                conn.commit()
                logger.info("已为 memories 表添加 chapter_num 列")
    except Exception as e:
        logger.warning(f"迁移 memories 表失败（可能列已存在）：{e}")

    # 迁移：为 chapters 表添加审计字段
    try:
        with engine.connect() as conn:
            for col_def in [
                ("audit_score", "INT NULL"),
                ("audit_result", "TEXT NULL"),
                ("rewrite_count", "INT DEFAULT 0"),
            ]:
                col_name, col_type = col_def
                result = conn.execute(text(
                    "SELECT COUNT(*) FROM information_schema.columns "
                    "WHERE table_schema = :db AND table_name = 'chapters' AND column_name = :col"
                ), {"db": MYSQL_DATABASE, "col": col_name})
                if result.scalar() == 0:
                    conn.execute(text(f"ALTER TABLE chapters ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info(f"已为 chapters 表添加 {col_name} 列")
    except Exception as e:
        logger.warning(f"迁移 chapters 表失败（可能列已存在）：{e}")

    # 迁移：为 characters 表添加 current_state 字段
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = :db AND table_name = 'characters' AND column_name = 'current_state'"
            ), {"db": MYSQL_DATABASE})
            if result.scalar() == 0:
                conn.execute(text("ALTER TABLE characters ADD COLUMN current_state TEXT NULL"))
                conn.commit()
                logger.info("已为 characters 表添加 current_state 列")
    except Exception as e:
        logger.warning(f"迁移 characters 表失败：{e}")

    # 迁移：为 novels 表添加 style_data 字段
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = :db AND table_name = 'novels' AND column_name = 'style_data'"
            ), {"db": MYSQL_DATABASE})
            if result.scalar() == 0:
                conn.execute(text("ALTER TABLE novels ADD COLUMN style_data TEXT NULL"))
                conn.commit()
                logger.info("已为 novels 表添加 style_data 列")
    except Exception as e:
        logger.warning(f"迁移 novels 表失败：{e}")

    # 迁移：为 novels 表添加 volume_plan 字段
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = :db AND table_name = 'novels' AND column_name = 'volume_plan'"
            ), {"db": MYSQL_DATABASE})
            if result.scalar() == 0:
                conn.execute(text("ALTER TABLE novels ADD COLUMN volume_plan TEXT NULL"))
                conn.commit()
                logger.info("已为 novels 表添加 volume_plan 列")
    except Exception as e:
        logger.warning(f"迁移 novels 表 volume_plan 失败：{e}")

    logger.info("数据表已同步")


def get_db():
    """FastAPI 依赖：获取数据库会话，请求结束自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
