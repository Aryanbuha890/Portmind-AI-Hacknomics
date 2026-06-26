"""
Vector Search Module
====================
Performs dense-vector similarity search against the ChromaDB
collection using the same embedding model used during ingestion.
"""

from typing import List, Optional, Tuple

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from src.utils.logger import log
from src.utils.config import get_settings


class VectorSearchEngine:
    """
    Thin wrapper around ChromaDB similarity search.

    Provides methods for:
        - Top-K similarity search
        - Similarity search with relevance scores
        - MMR (Maximal Marginal Relevance) search for diversity
    """

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ):
        """
        Initialise the vector search engine.

        Args:
            persist_dir:      Path to ChromaDB storage.
            collection_name:  Collection to query.
            embedding_model:  HuggingFace model for query encoding.
        """
        settings = get_settings()
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.chroma_collection_name
        self.top_k = settings.vector_search_top_k

        self._embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model or settings.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        self._vectorstore = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self._embeddings,
            collection_name=self.collection_name,
        )

        log.info("VectorSearchEngine connected to collection '{}'", self.collection_name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def search(self, query: str, top_k: Optional[int] = None) -> List[Document]:
        """
        Run a standard similarity search.

        Args:
            query: Natural-language question.
            top_k: Number of results (default from settings).

        Returns:
            Ranked list of Documents.
        """
        k = top_k or self.top_k
        log.debug("Vector search – query='{}', top_k={}", query[:80], k)
        results = self._vectorstore.similarity_search(query, k=k)
        log.info("Vector search returned {} result(s)", len(results))
        return results

    def search_with_scores(
        self, query: str, top_k: Optional[int] = None
    ) -> List[Tuple[Document, float]]:
        """
        Similarity search that also returns distance scores.

        Args:
            query: Natural-language question.
            top_k: Number of results.

        Returns:
            List of (Document, score) tuples – lower score = closer match.
        """
        k = top_k or self.top_k
        results = self._vectorstore.similarity_search_with_relevance_scores(query, k=k)
        log.info("Scored search returned {} result(s)", len(results))
        return results

    def mmr_search(
        self,
        query: str,
        top_k: Optional[int] = None,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
    ) -> List[Document]:
        """
        Maximal Marginal Relevance search for diverse results.

        Args:
            query:       Natural-language question.
            top_k:       Final number of results.
            fetch_k:     Candidates to fetch before MMR filtering.
            lambda_mult: Diversity vs relevance trade-off (0 = max diversity).

        Returns:
            Diverse ranked list of Documents.
        """
        k = top_k or self.top_k
        results = self._vectorstore.max_marginal_relevance_search(
            query, k=k, fetch_k=fetch_k, lambda_mult=lambda_mult
        )
        log.info("MMR search returned {} result(s)", len(results))
        return results

    def get_collection_count(self) -> int:
        """Return the number of vectors in the collection."""
        collection = self._vectorstore._collection
        return collection.count()
