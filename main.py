import os
import sys
import logging

# HuggingFace 国内镜像（必须在 sentence_transformers import 前设置）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, chat, knowledge, novel
from database import init_db

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="AI小说创作平台", version="2.0.0")

# CORS（开发期允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(auth.router)
app.include_router(knowledge.router)
app.include_router(chat.router)
app.include_router(novel.router)

# 静态文件（保留旧版 demo.html）
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    # 初始化数据库（自动建库建表）
    try:
        init_db()
    except Exception as e:
        logging.error(f"数据库初始化失败：{e}")
        logging.error("请检查 .env 中的 MySQL 连接配置（MYSQL_HOST/PORT/USER/PASSWORD）")
    print("\n" + "=" * 50)
    print("  AI小说创作平台启动成功！")
    print("  API 文档: http://localhost:8000/docs")
    print("  旧版演示: http://localhost:8000/static/demo.html")
    print("=" * 50 + "\n", file=sys.stderr)


@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "服务运行正常"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
