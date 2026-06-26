"""
Text Splitter Module
====================
Splits raw LangChain ``Document`` objects into smaller, overlapping
chunks suitable for embedding and retrieval.

Strategy:
    - **RecursiveCharacterTextSplitter** for general prose.
    - Chunk size and overlap are configured via ``.env``.
"""

from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from src.utils.logger import log
from src.utils.config import get_settings


class DocumentSplitter:
    """
    Splits documents into fixed-size overlapping chunks.

    Attributes:
        chunk_size:    Maximum characters per chunk.
        chunk_overlap: Number of overlapping characters between consecutive chunks.
    """

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None):
        """
        Initialise the splitter.

        Args:
            chunk_size:    Override chunk size (default from settings: 512).
            chunk_overlap: Override overlap   (default from settings: 50).
        """
        settings = get_settings()
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
            is_separator_regex=False,
        )

        log.info(
            "DocumentSplitter ready – chunk_size={}, overlap={}",
            self.chunk_size,
            self.chunk_overlap,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def split(self, documents: List[Document]) -> List[Document]:
        """
        Split a list of Documents into smaller chunks.

        Each resulting chunk inherits the metadata of its parent document
        and receives an additional ``chunk_index`` field.

        Args:
            documents: Raw page-level documents from the PDF loader.

        Returns:
            List of chunked ``Document`` objects.
        """
        if not documents:
            log.warning("No documents provided for splitting.")
            return []

        chunks = self._splitter.split_documents(documents)

        # Enrich chunks with positional metadata
        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = idx

        log.info(
            "Split {} document(s) into {} chunk(s)",
            len(documents),
            len(chunks),
        )
        return chunks

    def split_text(self, text: str) -> List[str]:
        """
        Split a plain string into chunk-sized pieces.

        Useful for ad-hoc text that isn't wrapped in a Document.

        Args:
            text: Raw text string.

        Returns:
            List of text chunks.
        """
        return self._splitter.split_text(text)
