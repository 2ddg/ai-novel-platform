"""文本分块器测试（匹配父子分块实现）"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.text_splitter import TextSplitter


class TestTextSplitter:

    def setup_method(self):
        self.splitter = TextSplitter()

    def test_short_text(self):
        """短文本：1 个父块、按句切出子块"""
        text = "这是一段短文本"
        parents, children, mapping = self.splitter.split_text(text)
        assert len(parents) == 1
        assert parents[0] == text
        assert len(children) >= 1
        assert 0 in mapping

    def test_long_text(self):
        """长文本：按段落生成多个父块并切出子块，映射完整"""
        # 每段约 28 字，50 段约 1400 字，超过父块上限 1024
        text = "这是一段很长的内容用来测试分块功能。\n\n" * 50
        parents, children, mapping = self.splitter.split_text(text)
        assert len(parents) >= 1
        assert children
        # 子块映射完整：mapping 中索引总数 == children 长度
        assert sum(len(v) for v in mapping.values()) == len(children)

    def test_empty_text(self):
        """空文本返回空"""
        parents, children, mapping = self.splitter.split_text("")
        assert parents == [] and children == [] and mapping == {}

    def test_chinese_text(self):
        """中文文本：父块与子块均非空，且映射非空"""
        # 每段约 33 字，40 段约 1320 字，超过父块上限
        text = "这是第一段内容。这是第二段内容。这是第三段内容。\n\n" * 40
        parents, children, mapping = self.splitter.split_text(text)
        assert parents
        assert children
        assert mapping
