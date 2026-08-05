"""BGE-small-zh 本地 Embedding 模型（sentence-transformers，懒加载）"""
import logging
from typing import List
from config import EMBEDDING_MODEL_PATH, EMBEDDING_DIM

logger = logging.getLogger(__name__)

# 全局模型实例（懒加载，首次调用才加载）
_model = None


def get_model():
    """获取模型实例（懒加载 sentence_transformers）"""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info(f"加载 Embedding 模型: {EMBEDDING_MODEL_PATH}")
        _model = SentenceTransformer(EMBEDDING_MODEL_PATH)
        logger.info("模型加载完成")
    return _model


def get_embedding(text: str) -> List[float]:
    """获取单条文本的 embedding"""
    model = get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """批量获取 embedding"""
    if not texts:
        return []
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
    return embeddings.tolist()
