"""
Hybrid Search Module
====================
Combines **dense vector search** (semantic) with **sparse BM25 search**
(keyword / lexical) to improve retrieval recall on maritime safety documents.

Strategy:
    1. Run vector search against ChromaDB.
    2. Run BM25 over all stored document chunks.
    3. Fuse results via Reciprocal Rank Fusion (RRF).
"""

from typing import List, Optional, Dict

from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from rank_bm25 import BM25Okapi
import torch

from src.utils.logger import log
from src.utils.config import get_settings


class HybridSearchEngine:
    """
    Merges dense and sparse retrieval for higher recall.

    Attributes:
        rrf_k:  Constant for Reciprocal Rank Fusion (default 60).
    """

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_model: Optional[str] = None,
        rrf_k: int = 60,
    ):
        """
        Initialise the hybrid search engine.

        Args:
            persist_dir:      ChromaDB directory.
            collection_name:  Collection to query.
            embedding_model:  HuggingFace model for dense retrieval.
            rrf_k:            RRF constant (higher → more weight on lower ranks).
        """
        settings = get_settings()
        self.top_k = settings.hybrid_search_top_k
        self.rrf_k = rrf_k

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model or settings.embedding_model,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True},
        )

        self._vectorstore = Chroma(
            persist_directory=persist_dir or settings.chroma_persist_dir,
            embedding_function=self._embeddings,
            collection_name=collection_name or settings.chroma_collection_name,
        )

        # BM25 index is built on application startup
        self._bm25_index: Optional[BM25Okapi] = None
        self._corpus_docs: List[Document] = []
        try:
            self._build_bm25_index()
        except Exception as e:
            log.warning("Failed to build BM25 index on startup: {}. Will retry on search.", e)

        log.info("HybridSearchEngine initialised (RRF k={})", self.rrf_k)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_bm25_index(self) -> None:
        """
        Fetch all documents from ChromaDB and build a BM25 index.

        This is called lazily on the first hybrid search call.
        """
        log.info("Building BM25 index from ChromaDB collection…")

        collection = self._vectorstore._collection
        result = collection.get(include=["documents", "metadatas"])

        self._corpus_docs = []
        tokenised_corpus: List[List[str]] = []

        for doc_text, meta in zip(result["documents"], result["metadatas"]):
            self._corpus_docs.append(
                Document(page_content=doc_text, metadata=meta or {})
            )
            tokenised_corpus.append(doc_text.lower().split())

        if tokenised_corpus:
            self._bm25_index = BM25Okapi(tokenised_corpus)
            log.info("BM25 index built over {} document(s)", len(tokenised_corpus))
        else:
            log.warning("No documents found – BM25 index is empty.")

    def _bm25_search(self, query: str, top_k: int) -> List[Document]:
        """Run BM25 keyword search over the corpus."""
        if self._bm25_index is None:
            self._build_bm25_index()

        if not self._corpus_docs:
            return []

        tokenised_query = query.lower().split()
        scores = self._bm25_index.get_scores(tokenised_query)

        # Pair docs with scores and sort descending
        scored = sorted(
            zip(self._corpus_docs, scores), key=lambda x: x[1], reverse=True
        )

        return [doc for doc, _ in scored[:top_k]]

    @staticmethod
    def _reciprocal_rank_fusion(
        ranked_lists: List[List[Document]], k: int = 60, top_k: int = 10
    ) -> List[Document]:
        """
        Merge multiple ranked lists via Reciprocal Rank Fusion.

        RRF score for document d = Σ 1 / (k + rank_i(d))

        Args:
            ranked_lists: List of independently ranked Document lists.
            k:            RRF constant.
            top_k:        Number of fused results to return.

        Returns:
            Fused, deduplicated list of Documents.
        """
        fused_scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}

        for ranked in ranked_lists:
            for rank, doc in enumerate(ranked, start=1):
                doc_id = doc.page_content[:200]  # Use content prefix as ID
                if doc_id not in doc_map:
                    doc_map[doc_id] = doc
                    fused_scores[doc_id] = 0.0
                fused_scores[doc_id] += 1.0 / (k + rank)

        sorted_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)
        return [doc_map[did] for did in sorted_ids[:top_k]]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def search(self, query: str, top_k: Optional[int] = None) -> List[Document]:
        """
        Run hybrid search: dense vector + BM25 keyword, fused via RRF.

        Args:
            query: Natural-language question.
            top_k: Number of fused results to return.

        Returns:
            Ranked list of Documents.
        """
        k = top_k or self.top_k
        log.info("Hybrid search – query='{}', top_k={}", query[:80], k)

        # 1. Dense vector search
        vector_results = self._vectorstore.similarity_search(query, k=k)
        log.debug("Vector leg returned {} result(s)", len(vector_results))

        # 2. Sparse BM25 search
        bm25_results = self._bm25_search(query, top_k=k)
        log.debug("BM25 leg returned {} result(s)", len(bm25_results))

        # 3. Fuse via RRF
        fused = self._reciprocal_rank_fusion(
            [vector_results, bm25_results], k=self.rrf_k, top_k=k
        )
        log.info("Hybrid search fused into {} result(s)", len(fused))
        return fused

    def refresh_bm25_index(self) -> None:
        """Force-rebuild the BM25 index (e.g. after new documents are ingested)."""
        self._bm25_index = None
        self._corpus_docs = []
        self._build_bm25_index()
