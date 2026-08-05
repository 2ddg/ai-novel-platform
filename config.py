import os
from dotenv import load_dotenv

load_dotenv()

# LLM配置
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
LLM_MODEL = "glm-4-flash"
LLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 成本感知路由：按任务复杂度选择模型
# glm-4-flash: 便宜快速，适合简单任务（提取、分类、摘要）
# glm-4: 强力但贵，适合复杂任务（正文生成、大纲规划）
# glm-4-air: 中间档，适合中等任务（审计、改写）
COST_AWARE_MODELS = {
    "cheap": "glm-4-flash",      # 简单任务：角色提取、情绪分析、伏笔扫描
    "medium": "glm-4-air",       # 中等任务：章节审计、文风分析
    "premium": "glm-4",          # 复杂任务：正文生成、大纲规划
}
DEFAULT_TIER = "cheap"

# Embedding配置（BGE-small-zh 本地模型，约 100MB，512 维）
EMBEDDING_MODEL_PATH = "./models/bge-small-zh-v1.5"
EMBEDDING_DIM = 512

# 向量数据库配置
VECTOR_DB_PATH = "./data/faiss_index"

# Reranker配置
RERANKER_MODEL_PATH = "BAAI/bge-reranker-v2-m3"

# 文档处理配置
UPLOAD_DIR = "./uploads"
PARENT_CHUNK_SIZE = 1024  # 父块大小
CHILD_CHUNK_SIZE = 256    # 子块大小
CHUNK_OVERLAP = 50

# 检索配置
TOP_K = 5
BM25_WEIGHT = 0.3  # BM25权重
VECTOR_WEIGHT = 0.7  # 向量检索权重

# ============ MySQL 数据库配置 ============
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "rag_knowledge_base")

# SQLAlchemy 连接串（pymysql 驱动）
DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
)

# ============ JWT 认证配置 ============
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "rag-kb-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 默认1天
