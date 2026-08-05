# 知识库问答系统

基于 RAG（检索增强生成）的文档知识库问答系统，支持PDF/TXT/MD文档上传、向量化存储、智能问答。

## 功能特性

- 支持PDF/TXT/MD文档上传和解析
- 智谱Embedding API向量化
- ChromaDB向量存储
- RAG检索增强生成
- 流式问答输出（SSE）
- 多知识库管理

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置API Key
cp .env.example .env
# 编辑 .env 文件，填入你的智谱API Key

# 3. 启动服务
python main.py
```

访问 http://localhost:8001/demo.html

## 技术架构

```
用户提问 → Embedding向量化 → ChromaDB检索 → 构建Prompt → LLM生成回答
```

## 项目结构

```
项目三/
├── main.py              # FastAPI入口
├── config.py            # 配置
├── core/                # 核心模块
│   ├── llm_client.py    # LLM调用
│   ├── embeddings.py    # Embedding服务
│   ├── vector_store.py  # 向量存储
│   └── rag_engine.py    # RAG引擎
├── routers/             # API路由
├── static/              # 前端页面
└── tests/               # 单元测试
```
