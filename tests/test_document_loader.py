"""文档加载器测试"""
import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.document_loader import DocumentLoader


class TestDocumentLoader:
    
    def setup_method(self):
        self.loader = DocumentLoader()
    
    def test_load_txt(self):
        """加载TXT文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("这是一个测试文件的内容")
            temp_path = f.name
        
        try:
            docs = self.loader.load_file(temp_path)
            assert len(docs) == 1
            assert docs[0].content == "这是一个测试文件的内容"
            assert docs[0].metadata["filename"].endswith(".txt")
        finally:
            os.unlink(temp_path)
    
    def test_load_md(self):
        """加载MD文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# 标题\n\n这是内容")
            temp_path = f.name
        
        try:
            docs = self.loader.load_file(temp_path)
            assert len(docs) == 1
        finally:
            os.unlink(temp_path)
    
    def test_unsupported_format(self):
        """不支持的格式"""
        try:
            self.loader.load_file("test.xyz")
            assert False, "应该抛出异常"
        except ValueError as e:
            assert "不支持" in str(e)
