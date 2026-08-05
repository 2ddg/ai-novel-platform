"""RAG检索增强生成引擎 - 混合检索 + Reranker"""
import json
import logging
from typing import List, Dict, Any, AsyncGenerator
from rank_bm25 import BM25Okapi
import jieba

from core.embeddings import get_embedding, get_embeddings_batch
from core.vector_store import get_vector_store
from core.text_splitter import TextSplitter
from core.document_loader import DocumentLoader
from core.llm_client import call_llm, call_llm_stream
from config import TOP_K, BM25_WEIGHT, VECTOR_WEIGHT, RERANKER_MODEL_PATH

logger = logging.getLogger(__name__)

# Reranker模型（懒加载；加载失败则降级为不重排序）
_reranker = None
_reranker_load_attempted = False


def get_reranker():
    """获取Reranker模型，加载失败返回 None（降级为仅用 RRF 融合）"""
    global _reranker, _reranker_load_attempted
    if _reranker_load_attempted:
        return _reranker
    _reranker_load_attempted = True
    try:
        from sentence_transformers import CrossEncoder
        logger.info(f"加载Reranker模型: {RERANKER_MODEL_PATH}")
        _reranker = CrossEncoder(RERANKER_MODEL_PATH)
        logger.info("Reranker加载完成")
    except Exception as e:
        logger.warning(f"Reranker 加载失败，降级为仅 RRF 融合: {e}")
        _reranker = None
    return _reranker


class RAGEngine:
    """RAG检索增强生成引擎（绑定单个知识库 collection）"""

    def __init__(self, collection_name: str = "default"):
        self.collection_name = collection_name
        self.vector_store = get_vector_store(collection_name)
        self.text_splitter = TextSplitter()
        self.document_loader = DocumentLoader()

    async def load_documents(self, file_path: str, document_id: int = 0, original_filename: str = None) -> Dict:
        """加载并处理文档"""
        # 1. 加载文档
        documents = self.document_loader.load_file(file_path, original_filename=original_filename)

        # 2. 父子分块
        result = self.text_splitter.split_documents(documents)
        child_chunks = result["child_chunks"]
        metadata = result["metadata"]

        # 注入文档ID到每个分块的metadata
        if document_id:
            for m in metadata:
                m["document_id"] = document_id

        # 3. 获取Embedding（批量调用智谱 API，按 64 条/批分片避免单次过大）
        embeddings = []
        batch_size = 64
        for i in range(0, len(child_chunks), batch_size):
            batch = child_chunks[i:i + batch_size]
            embeddings.extend(get_embeddings_batch(batch))

        # 4. 存储到 FAISS（存储子块）
        count = self.vector_store.add_documents(child_chunks, embeddings, metadata)

        return {
            "chunks_count": count,
            "parent_chunks": len(result["parent_chunks"]),
            "child_chunks": len(child_chunks)
        }

    async def query(self, question: str, top_k: int = TOP_K, rewrite: bool = True) -> Dict[str, Any]:
        """混合检索 + Reranker + 查询改写"""
        trace_id = self._gen_trace_id()

        # 0. 查询改写/扩展
        original_query = question
        expanded_queries = [question]
        if rewrite:
            expanded_queries = await self._query_rewrite(question)
            logger.info(f"[{trace_id}] 查询改写: 原查询='{question[:50]}', 扩展={len(expanded_queries)}条")

        # 1. 多查询向量检索
        all_vector_results = []
        for q in expanded_queries:
            query_embedding = get_embedding(q)
            results = self.vector_store.search(query_embedding, top_k=top_k * 2)
            all_vector_results.extend(results)

        # 去重合并
        seen = set()
        vector_results = []
        for r in all_vector_results:
            key = r["content"][:100]
            if key not in seen:
                seen.add(key)
                vector_results.append(r)

        # 2. BM25检索（用原查询）
        bm25_results = self._bm25_search(original_query, top_k=top_k * 2)

        # 3. RRF融合
        merged_results = self._rrf_fusion(vector_results, bm25_results)

        # 4. Reranker重排序
        reranked_results = self._rerank(original_query, merged_results, top_k=top_k)

        # 5. 构建上下文
        context = self._build_context(reranked_results)

        # 6. 调用LLM
        prompt = self._build_prompt(original_query, context)
        answer = await call_llm(prompt)

        # 7. 记录可观测性
        self._record_query_metrics(trace_id, original_query, len(reranked_results), len(answer))

        return {
            "answer": answer,
            "sources": [
                {
                    "content": r["content"][:200] + "..." if len(r["content"]) > 200 else r["content"],
                    "filename": r["metadata"].get("filename", "未知"),
                    "score": round(r.get("score", 0), 3)
                }
                for r in reranked_results
            ],
            "trace_id": trace_id,
            "expanded_queries": expanded_queries if rewrite else None,
        }

    def _bm25_search(self, query: str, top_k: int = 10) -> List[Dict]:
        """BM25关键词检索"""
        all_docs = self.vector_store.get_all_texts()
        if not all_docs:
            return []

        # 分词
        corpus = [list(jieba.cut(doc["content"])) for doc in all_docs]
        query_tokens = list(jieba.cut(query))

        # BM25检索
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(query_tokens)

        # 排序
        scored_docs = []
        for i, score in enumerate(scores):
            if score > 0:
                scored_docs.append({
                    "content": all_docs[i]["content"],
                    "metadata": all_docs[i]["metadata"],
                    "bm25_score": float(score)
                })

        scored_docs.sort(key=lambda x: x["bm25_score"], reverse=True)
        return scored_docs[:top_k]

    def _rrf_fusion(self, vector_results: List[Dict], bm25_results: List[Dict],
                    k: int = 60) -> List[Dict]:
        """RRF（Reciprocal Rank Fusion）融合算法"""
        scores = {}
        content_map = {}

        # 向量检索结果
        for rank, doc in enumerate(vector_results):
            key = doc["content"][:100]  # 用前100字符作为key
            scores[key] = scores.get(key, 0) + VECTOR_WEIGHT / (k + rank + 1)
            content_map[key] = doc

        # BM25检索结果
        for rank, doc in enumerate(bm25_results):
            key = doc["content"][:100]
            scores[key] = scores.get(key, 0) + BM25_WEIGHT / (k + rank + 1)
            content_map[key] = doc

        # 按融合分数排序
        sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        results = []
        for key in sorted_keys:
            doc = content_map[key]
            doc["score"] = scores[key]
            results.append(doc)

        return results

    def _rerank(self, query: str, results: List[Dict], top_k: int = 5) -> List[Dict]:
        """Reranker 重排序；模型不可用时降级为 RRF 分数排序"""
        if not results:
            return []

        reranker = get_reranker()
        if reranker is None:
            # 降级：直接用 RRF 融合分数排序
            results.sort(key=lambda x: x.get("score", 0), reverse=True)
            return results[:top_k]

        # 构建query-document对
        pairs = [(query, doc["content"]) for doc in results]

        # 计算相关性分数
        scores = reranker.predict(pairs)

        # 排序
        for i, score in enumerate(scores):
            results[i]["rerank_score"] = float(score)

        results.sort(key=lambda x: x["rerank_score"], reverse=True)

        return results[:top_k]

    def _build_context(self, results: List[Dict]) -> str:
        """构建检索上下文"""
        if not results:
            return "（未找到相关文档）"

        context = "以下是与问题相关的参考资料：\n\n"
        for i, r in enumerate(results):
            context += f"【资料{i+1}】(来源: {r['metadata'].get('filename', '未知')})\n"
            context += r["content"] + "\n\n"

        return context

    def _build_prompt(self, question: str, context: str) -> str:
        """构建RAG提示词"""
        return (
            "你是一个专业的知识问答助手。请基于以下参考资料回答用户的问题。\n\n"
            "要求：\n"
            "1. 优先使用参考资料中的信息回答\n"
            "2. 如果参考资料不足以回答，请明确说明\n"
            "3. 回答要准确、简洁\n\n"
            f"{context}\n"
            f"【用户问题】\n{question}"
        )

    # ============ 查询改写/扩展 ============

    async def _query_rewrite(self, question: str) -> List[str]:
        """查询改写：生成多个不同表述的查询以提升召回率"""
        try:
            prompt = (
                "你是一个查询改写专家。请将用户的问题改写为3种不同的表述方式，"
                "要求保持原意但使用不同的关键词和句式，以最大化文档检索召回率。\n\n"
                f"原问题：{question}\n\n"
                "请直接输出3个改写后的问题，每行一个，不要编号或其他文字："
            )
            result = await call_llm(prompt, temperature=0.3, max_tokens=300)
            queries = [q.strip() for q in result.strip().split("\n") if q.strip()]
            if len(queries) >= 2:
                return queries[:3]
        except Exception as e:
            logger.warning(f"查询改写失败，使用原查询: {e}")
        return [question]

    # ============ 可观测性 ============

    _query_metrics = []

    @staticmethod
    def _gen_trace_id() -> str:
        import uuid
        return uuid.uuid4().hex[:12]

    def _record_query_metrics(self, trace_id: str, query: str, source_count: int, answer_len: int):
        """记录查询指标到内存（生产环境可接入Prometheus/ELK）"""
        entry = {
            "trace_id": trace_id,
            "query": query[:100],
            "source_count": source_count,
            "answer_length": answer_len,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }
        self._query_metrics.append(entry)
        if len(self._query_metrics) > 1000:
            self._query_metrics = self._query_metrics[-500:]

    def get_metrics(self) -> List[Dict]:
        """获取查询指标历史"""
        return self._query_metrics.copy()

    async def query_stream(self, question: str, top_k: int = TOP_K, rewrite: bool = True) -> AsyncGenerator[str, None]:
        """流式查询（支持查询改写）"""
        trace_id = self._gen_trace_id()
        original_query = question
        expanded_queries = [question]
        if rewrite:
            expanded_queries = await self._query_rewrite(question)

        # 多查询向量检索
        all_vector_results = []
        for q in expanded_queries:
            query_embedding = get_embedding(q)
            results = self.vector_store.search(query_embedding, top_k=top_k * 2)
            all_vector_results.extend(results)

        seen = set()
        vector_results = []
        for r in all_vector_results:
            key = r["content"][:100]
            if key not in seen:
                seen.add(key)
                vector_results.append(r)

        bm25_results = self._bm25_search(original_query, top_k=top_k * 2)
        merged_results = self._rrf_fusion(vector_results, bm25_results)
        reranked_results = self._rerank(original_query, merged_results, top_k=top_k)

        sources = [
            {
                "content": r["content"][:200] + "..." if len(r["content"]) > 200 else r["content"],
                "filename": r["metadata"].get("filename", "未知"),
                "score": round(r.get("score", 0), 3)
            }
            for r in reranked_results
        ]
        yield f"[SOURCES]{json.dumps(sources)}"

        context = self._build_context(reranked_results)
        prompt = self._build_prompt(original_query, context)
        async for chunk in call_llm_stream(prompt):
            yield chunk

        self._record_query_metrics(trace_id, original_query, len(reranked_results), 0)
