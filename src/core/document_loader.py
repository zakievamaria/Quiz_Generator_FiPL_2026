import os
from pathlib import Path
from typing import List, Dict, Optional


class DocumentLoader:
    """
    Loads text from 1 to 10 files in .txt or .docx format.
    The files are assumed to contain French text, but the class itself
    only handles extraction – language‑specific processing is left to the caller.
    """

    def __init__(self, file_paths: Optional[List[str]] = None):
        """
        :param file_paths: Optional list of file paths to load.
                           If not provided, you can set them later with set_files().
        """
        self.file_paths = file_paths or []
        self.validate_file_paths()

    def set_files(self, file_paths: List[str]) -> None:
        """Set or replace the list of files to load."""
        self.file_paths = file_paths
        self.validate_file_paths()

    def validate_file_paths(self) -> None:
        """Check that there are 1–10 files, that each exists, and that the extension is .txt or .docx."""
        if not (1 <= len(self.file_paths) <= 10):
            raise ValueError("Number of files must be between 1 and 10 inclusive.")

        for path in self.file_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")

            ext = Path(path).suffix.lower()
            if ext not in ('.txt', '.docx'):
                raise ValueError(f"Unsupported file format: {ext}. Only .txt and .docx are allowed.")

    def load(self) -> List[Dict]:
        """
        Load all files and return a list of dictionaries.
        Each dictionary contains:
            - file_path: str
            - content:   str   (the extracted text)
            - size:      int   (character count)
            - extension: str   ('.txt' or '.docx')
        """
        documents = []
        for path in self.file_paths:
            ext = Path(path).suffix.lower()
            if ext == '.txt':
                content = self._read_txt(path)
            elif ext == '.docx':
                content = self._read_docx(path)
            else:
                # Should never happen due to validation, but keep as safety.
                continue

            documents.append({
                'file_path': path,
                'content': content,
                'size': len(content),
                'extension': ext
            })
        return documents

    @staticmethod
    def _read_txt(path: str) -> str:
        """Read a plain text file with UTF‑8 encoding."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def _read_docx(path: str) -> str:
        """Read a .docx file using python-docx."""
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "Reading .docx files requires python-docx. "
                "Install it with: pip install python-docx"
            )

        doc = Document(path)
        return '\n'.join(para.text for para in doc.paragraphs)