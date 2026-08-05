import os
import json
from typing import List
from dataclasses import dataclass


@dataclass
class Document:
    """文档对象"""
    content: str
    metadata: dict


class DocumentLoader:
    """文档加载器 - 支持 TXT/MD/PDF/DOC/DOCX/HTML/JSON/CSV"""

    def load_file(self, file_path: str, original_filename: str = None) -> List[Document]:
        """加载单个文件"""
        ext = os.path.splitext(file_path)[1].lower()
        filename = original_filename or os.path.basename(file_path)

        if ext in ['.txt', '.md']:
            return self._load_text(file_path, filename)
        elif ext == '.pdf':
            return self._load_pdf(file_path, filename)
        elif ext in ['.doc', '.docx']:
            return self._load_docx(file_path, filename)
        elif ext == '.html':
            return self._load_html(file_path, filename)
        elif ext == '.json':
            return self._load_json(file_path, filename)
        elif ext == '.csv':
            return self._load_csv(file_path, filename)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

    def load_files(self, file_paths: List[str]) -> List[Document]:
        """批量加载文件"""
        documents = []
        for path in file_paths:
            documents.extend(self.load_file(path))
        return documents

    def _get_ext(self, file_path: str) -> str:
        return os.path.splitext(file_path)[1].lower()

    def _load_text(self, file_path: str, filename: str) -> List[Document]:
        """加载 TXT/MD 文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return [Document(content=content, metadata={"filename": filename})]

    def _load_pdf(self, file_path: str, filename: str) -> List[Document]:
        """加载 PDF 文件"""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            documents = []

            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    documents.append(Document(
                        content=text,
                        metadata={"filename": filename, "page": page_num + 1}
                    ))

            return documents
        except Exception as e:
            raise Exception(f"PDF加载失败: {str(e)}")

    def _load_docx(self, file_path: str, filename: str) -> List[Document]:
        """加载 DOC/DOCX 文件"""
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(file_path)
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            content = '\n\n'.join(paragraphs)
            if not content:
                raise Exception("文档内容为空")
            return [Document(content=content, metadata={"filename": filename})]
        except Exception as e:
            raise Exception(f"DOCX加载失败: {str(e)}")

    def _load_html(self, file_path: str, filename: str) -> List[Document]:
        """加载 HTML 文件"""
        try:
            from bs4 import BeautifulSoup
            with open(file_path, 'r', encoding='utf-8') as f:
                html = f.read()
            soup = BeautifulSoup(html, 'html.parser')
            # 移除 script 和 style 标签
            for tag in soup(['script', 'style']):
                tag.decompose()
            content = soup.get_text(separator='\n', strip=True)
            if not content:
                raise Exception("HTML内容为空")
            return [Document(content=content, metadata={"filename": filename})]
        except Exception as e:
            raise Exception(f"HTML加载失败: {str(e)}")

    def _load_json(self, file_path: str, filename: str) -> List[Document]:
        """加载 JSON 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            content = json.dumps(data, ensure_ascii=False, indent=2)
            return [Document(content=content, metadata={"filename": filename})]
        except Exception as e:
            raise Exception(f"JSON加载失败: {str(e)}")

    def _load_csv(self, file_path: str, filename: str) -> List[Document]:
        """加载 CSV 文件"""
        try:
            import csv
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            content = '\n'.join([','.join(row) for row in rows])
            return [Document(content=content, metadata={"filename": filename})]
        except Exception as e:
            raise Exception(f"CSV加载失败: {str(e)}")
