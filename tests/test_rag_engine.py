"""RAG引擎测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rag_engine import RAGEngine


class TestRAGEngine:
    
    def setup_method(self):
        self.engine = RAGEngine()
    
    def test_build_context(self):
        """测试上下文构建"""
        results = [
            {"content": "测试内容1", "metadata": {"filename": "test.txt"}, "similarity": 0.9},
            {"content": "测试内容2", "metadata": {"filename": "test2.txt"}, "similarity": 0.8}
        ]
        context = self.engine._build_context(results)
        assert "测试内容1" in context
        assert "测试内容2" in context
        assert "参考资料" in context
    
    def test_build_context_empty(self):
        """空结果构建上下文"""
        context = self.engine._build_context([])
        assert "未找到" in context
    
    def test_build_prompt(self):
        """测试prompt构建"""
        prompt = self.engine._build_prompt("什么是AI", "参考资料内容")
        assert "AI" in prompt
        assert "参考资料内容" in prompt
        assert "用户问题" in prompt
