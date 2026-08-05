"""父子分块策略"""
import re
from typing import List, Dict, Tuple
from config import PARENT_CHUNK_SIZE, CHILD_CHUNK_SIZE, CHUNK_OVERLAP


class TextSplitter:
    """父子分块器"""

    def __init__(self):
        self.parent_size = PARENT_CHUNK_SIZE
        self.child_size = CHILD_CHUNK_SIZE
        self.overlap = CHUNK_OVERLAP

    def split_text(self, text: str) -> Tuple[List[str], List[str], Dict[int, List[int]]]:
        """
        将文本分块为父子块
        返回: (parent_chunks, child_chunks, parent_child_mapping)
        """
        if not text:
            return [], [], {}

        # 先按段落分割
        paragraphs = re.split(r'\n\n+', text)

        # 生成父块
        parent_chunks = self._split_by_size(paragraphs, self.parent_size)

        # 生成子块，并建立映射关系
        child_chunks = []
        parent_child_mapping = {}  # parent_index -> [child_indices]

        for parent_idx, parent_chunk in enumerate(parent_chunks):
            # 将父块按句子分割成子块
            child_indices = []
            children = self._split_by_size(
                re.split(r'(?<=[。！？；\n])', parent_chunk),
                self.child_size
            )

            for child in children:
                child_idx = len(child_chunks)
                child_chunks.append(child)
                child_indices.append(child_idx)

            parent_child_mapping[parent_idx] = child_indices

        return parent_chunks, child_chunks, parent_child_mapping

    def _split_by_size(self, segments: List[str], target_size: int) -> List[str]:
        """按目标大小合并段落"""
        chunks = []
        buffer = ""

        for seg in segments:
            if not seg.strip():
                continue

            # 单个段落就超限，强制切分
            if len(seg) > target_size:
                if buffer.strip():
                    chunks.append(buffer.strip())
                    buffer = ""
                for i in range(0, len(seg), target_size - self.overlap):
                    chunk = seg[i:i + target_size]
                    if chunk.strip():
                        chunks.append(chunk.strip())
                continue

            if len(buffer) + len(seg) > target_size and buffer:
                chunks.append(buffer.strip())
                tail = buffer[-self.overlap:] if len(buffer) > self.overlap else buffer
                buffer = tail
            buffer += seg

        if buffer.strip():
            chunks.append(buffer.strip())

        return chunks

    def split_documents(self, documents: list) -> Dict:
        """分割文档列表，返回结构化结果"""
        all_parent_chunks = []
        all_child_chunks = []
        all_mapping = {}
        all_metadata = []

        for doc in documents:
            parents, children, mapping = self.split_text(doc.content)

            # 调整索引偏移
            parent_offset = len(all_parent_chunks)
            child_offset = len(all_child_chunks)

            all_parent_chunks.extend(parents)
            all_child_chunks.extend(children)

            for parent_idx, child_indices in mapping.items():
                new_parent_idx = parent_idx + parent_offset
                new_child_indices = [idx + child_offset for idx in child_indices]
                all_mapping[new_parent_idx] = new_child_indices

            # 为每个子块添加元数据
            for i in range(len(children)):
                all_metadata.append({
                    **doc.metadata,
                    "chunk_type": "child",
                    "parent_offset": parent_offset
                })

        return {
            "parent_chunks": all_parent_chunks,
            "child_chunks": all_child_chunks,
            "mapping": all_mapping,
            "metadata": all_metadata
        }
