"""FAISS 向量存储封装（支持多知识库 collection）

每个知识库对应一个独立的 FAISS 索引文件，互不干扰。
"""
import os
import json
import logging
import faiss
import numpy as np
from typing import List, Dict
from config import VECTOR_DB_PATH, EMBEDDING_DIM

logger = logging.getLogger(__name__)

_store_cache: Dict[str, "VectorStore"] = {}


class VectorStore:
    """FAISS 向量存储封装（单知识库）"""

    def __init__(self, collection_name: str = "default"):
        self.collection_name = collection_name
        self.base_dir = VECTOR_DB_PATH
        os.makedirs(self.base_dir, exist_ok=True)
        self.index_path = os.path.join(self.base_dir, f"{collection_name}.index")
        self.meta_path = os.path.join(self.base_dir, f"{collection_name}.index.meta")
        self.index = None
        self.texts: List[str] = []
        self.metadata: List[Dict] = []
        self.vectors: List[List[float]] = []
        self._load()

    def _load(self):
        """加载已有索引"""
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.texts = data.get("texts", [])
                self.metadata = data.get("metadata", [])
                self.vectors = data.get("vectors", [])
        else:
            self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
            self.texts = []
            self.metadata = []
            self.vectors = []

    def _save(self):
        """保存索引"""
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "texts": self.texts,
                "metadata": self.metadata,
                "vectors": self.vectors,
            }, f, ensure_ascii=False)

    def add_documents(self, chunks: List[str], embeddings: List[List[float]],
                      metadata: List[Dict]) -> int:
        """添加文档到向量库"""
        vectors = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.texts.extend(chunks)
        self.metadata.extend(metadata)
        self.vectors.extend(embeddings)
        self._save()
        return len(chunks)

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """向量检索"""
        if self.index.ntotal == 0:
            return []

        query = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query)

        scores, indices = self.index.search(query, min(top_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.texts):
                continue
            results.append({
                "content": self.texts[idx],
                "metadata": self.metadata[idx],
                "score": float(score)
            })

        return results

    def get_all_texts(self) -> List[Dict]:
        """获取所有文档文本（用于 BM25 检索）"""
        return [{"content": t, "metadata": m} for t, m in zip(self.texts, self.metadata)]

    def delete_collection(self) -> bool:
        """删除当前 collection 的索引文件"""
        try:
            for path in (self.index_path, self.meta_path):
                if os.path.exists(path):
                    os.remove(path)
            self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
            self.texts = []
            self.metadata = []
            self.vectors = []
            return True
        except Exception as e:
            logger.error(f"删除 collection 失败: {e}")
            return False

    def delete_document_chunks(self, document_id: int) -> int:
        """删除指定文档的所有向量分块，返回删除数量"""
        try:
            indices_to_keep = [
                i for i, meta in enumerate(self.metadata)
                if meta.get("document_id") != document_id
            ]

            deleted_count = len(self.texts) - len(indices_to_keep)
            if deleted_count == 0:
                return 0

            self.texts = [self.texts[i] for i in indices_to_keep]
            self.metadata = [self.metadata[i] for i in indices_to_keep]
            self.vectors = [self.vectors[i] for i in indices_to_keep]

            new_index = faiss.IndexFlatIP(EMBEDDING_DIM)
            if self.vectors:
                vec_array = np.array(self.vectors, dtype=np.float32)
                faiss.normalize_L2(vec_array)
                new_index.add(vec_array)

            self.index = new_index
            self._save()
            return deleted_count
        except Exception as e:
            logger.error(f"删除文档分块失败: {e}")
            return 0

    def delete_by_filename(self, filename: str) -> int:
        """按文件名删除分块（兜底：旧数据可能没有 document_id）
        
        兼容旧数据格式：旧数据 filename 带时间戳前缀（如 1785808375_移动端.pdf），
        新数据 filename 是原始文件名（如 移动端.pdf）。
        """
        try:
            indices_to_keep = []
            for i, meta in enumerate(self.metadata):
                meta_filename = meta.get("filename", "")
                # 精确匹配 或 以 _filename 结尾（兼容旧的时间戳前缀格式）
                if meta_filename == filename or meta_filename.endswith(f"_{filename}"):
                    continue  # 要删除的
                indices_to_keep.append(i)

            deleted_count = len(self.texts) - len(indices_to_keep)
            if deleted_count == 0:
                return 0

            self.texts = [self.texts[i] for i in indices_to_keep]
            self.metadata = [self.metadata[i] for i in indices_to_keep]
            self.vectors = [self.vectors[i] for i in indices_to_keep]

            new_index = faiss.IndexFlatIP(EMBEDDING_DIM)
            if self.vectors:
                vec_array = np.array(self.vectors, dtype=np.float32)
                faiss.normalize_L2(vec_array)
                new_index.add(vec_array)

            self.index = new_index
            self._save()
            return deleted_count
        except Exception as e:
            logger.error(f"按文件名删除分块失败: {e}")
            return 0

    def get_count(self) -> int:
        """获取文档数量"""
        return len(self.texts)


def get_vector_store(collection_name: str) -> VectorStore:
    """获取指定知识库的 VectorStore（带缓存）"""
    if collection_name not in _store_cache:
        _store_cache[collection_name] = VectorStore(collection_name)
    return _store_cache[collection_name]


def remove_vector_store(collection_name: str):
    """从缓存中移除并删除某个知识库的向量数据"""
    store = _store_cache.pop(collection_name, None)
    if store is None:
        store = VectorStore(collection_name)
    store.delete_collection()