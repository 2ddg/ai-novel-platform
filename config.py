import os
from dotenv import load_dotenv

load_dotenv()

# LLM配置
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
LLM_MODEL = "glm-4-flash"
LLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

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
