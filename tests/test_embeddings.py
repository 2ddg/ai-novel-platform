"""Embedding测试"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.embeddings import get_embedding, get_embeddings_batch


class TestEmbeddings:
    
    def test_single_embedding(self):
        """单条文本embedding"""
        result = asyncio.run(get_embedding("测试文本"))
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_batch_embeddings(self):
        """批量embedding"""
        texts = ["文本1", "文本2", "文本3"]
        results = asyncio.run(get_embeddings_batch(texts))
        assert len(results) == 3
        assert all(isinstance(r, list) for r in results)
