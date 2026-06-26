"""
PDF Loader Module
=================
Loads one or many PDF documents from disk and converts them into
LangChain ``Document`` objects with rich metadata.

Supported libraries:
    - **pypdf** (default) – fast, pure-Python.
    - **pdfplumber** – better table / layout extraction.
"""

from pathlib import Path
from typing import List, Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from src.utils.logger import log
from src.utils.config import get_settings


class PDFDocumentLoader:
    """
    Loads PDF files from a directory or a single file path.

    Attributes:
        source_dir: Directory containing PDF files.
    """

    def __init__(self, source_dir: Optional[str] = None):
        """
        Initialise the PDF loader.

        Args:
            source_dir: Path to the directory of PDFs.
                         Defaults to ``data/raw_pdfs`` from settings.
        """
        settings = get_settings()
        self.source_dir = Path(source_dir) if source_dir else settings.raw_pdfs_dir
        log.info("PDFDocumentLoader initialised – source_dir={}", self.source_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def load_single(self, file_path: str | Path) -> List[Document]:
        """
        Load a single PDF and return a list of page-level Documents.

        Args:
            file_path: Absolute or relative path to the PDF.

        Returns:
            List of ``Document`` objects, one per page.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            log.error("PDF not found: {}", file_path)
            raise FileNotFoundError(f"PDF not found: {file_path}")

        log.info("Loading PDF: {}", file_path.name)
        loader = PyPDFLoader(str(file_path))
        docs = loader.load()

        # Enrich metadata with source filename
        for doc in docs:
            doc.metadata["source_file"] = file_path.name
            doc.metadata["file_path"] = str(file_path)

        log.info("Loaded {} pages from {}", len(docs), file_path.name)
        return docs

    def load_directory(self) -> List[Document]:
        """
        Load **all** PDFs in ``self.source_dir`` recursively.

        Returns:
            Combined list of Documents across all PDFs.
        """
        if not self.source_dir.exists():
            log.warning("Source directory does not exist – creating: {}", self.source_dir)
            self.source_dir.mkdir(parents=True, exist_ok=True)
            return []

        pdf_files = sorted(self.source_dir.glob("**/*.pdf"))
        if not pdf_files:
            log.warning("No PDF files found in {}", self.source_dir)
            return []

        log.info("Found {} PDF(s) in {}", len(pdf_files), self.source_dir)

        all_docs: List[Document] = []
        for pdf_path in pdf_files:
            try:
                docs = self.load_single(pdf_path)
                all_docs.extend(docs)
            except Exception as exc:
                log.error("Failed to load {}: {}", pdf_path.name, exc)

        log.info("Total documents loaded: {}", len(all_docs))
        return all_docs

    def get_available_pdfs(self) -> List[str]:
        """Return a list of PDF filenames available in the source directory."""
        if not self.source_dir.exists():
            return []
        return [p.name for p in sorted(self.source_dir.glob("**/*.pdf"))]
