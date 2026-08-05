"""文本分块器测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.text_splitter import TextSplitter


class TestTextSplitter:
    
    def setup_method(self):
        self.splitter = TextSplitter(chunk_size=100, overlap=20)
    
    def test_short_text(self):
        """短文本不分块"""
        text = "这是一段短文本"
        chunks = self.splitter.split_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_long_text(self):
        """长文本正确分块"""
        # 创建足够长的文本（每个段落约30字，共10段）
        text = "这是一段很长的内容用来测试分块功能。\n\n" * 10
        chunks = self.splitter.split_text(text)
        # 文本总长约300字，chunk_size=100，应该分成多块
        assert len(chunks) >= 2
    
    def test_empty_text(self):
        """空文本返回空列表"""
        chunks = self.splitter.split_text("")
        assert chunks == []
    
    def test_chinese_text(self):
        """中文文本分块"""
        text = "这是第一段内容。这是第二段内容。这是第三段内容。" * 10
        chunks = self.splitter.split_text(text)
        assert len(chunks) > 0
