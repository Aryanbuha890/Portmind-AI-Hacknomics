"""
Embedder Module
===============
Generates dense vector embeddings using HuggingFace sentence-transformers
and persists them in a ChromaDB vector store.

Default model: ``BAAI/bge-small-en-v1.5`` (384-dim, fast, high quality).
"""

from typing import List, Optional

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import torch

from src.utils.logger import log
from src.utils.config import get_settings


class DocumentEmbedder:
    """
    Embeds document chunks and upserts them into ChromaDB.

    Attributes:
        embedding_model: HuggingFace model identifier.
        collection_name: ChromaDB collection name.
    """

    def __init__(
        self,
        embedding_model: Optional[str] = None,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        """
        Initialise embedder and vector store connection.

        Args:
            embedding_model:  Override HuggingFace model name.
            persist_dir:      Override ChromaDB persistence directory.
            collection_name:  Override collection name.
        """
        settings = get_settings()

        self.embedding_model = embedding_model or settings.embedding_model
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.chroma_collection_name

        # Initialise the embedding function
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True},
        )

        log.info(
            "DocumentEmbedder ready – model={}, persist={}",
            self.embedding_model,
            self.persist_dir,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def embed_and_store(self, chunks: List[Document]) -> Chroma:
        """
        Embed document chunks and persist them in ChromaDB.

        Args:
            chunks: Pre-split Document objects.

        Returns:
            A ``Chroma`` vector store instance backed by the persisted data.
        """
        if not chunks:
            log.warning("No chunks to embed.")
            return self._get_vectorstore()

        log.info("Embedding {} chunk(s) into ChromaDB…", len(chunks))

        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self._embeddings,
            persist_directory=self.persist_dir,
            collection_name=self.collection_name,
        )

        log.info("Embeddings persisted to {}", self.persist_dir)
        return vectorstore

    def get_embedding_function(self) -> HuggingFaceEmbeddings:
        """Return the underlying HuggingFace embedding function."""
        return self._embeddings

    def _get_vectorstore(self) -> Chroma:
        """Open an existing ChromaDB vector store (read-only)."""
        return Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self._embeddings,
            collection_name=self.collection_name,
        )

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query string.

        Args:
            text: The query text.

        Returns:
            Dense vector (list of floats).
        """
        return self._embeddings.embed_query(text)
