import time
from typing import List, Tuple, Optional
from langchain_core.documents import Document

from src.retrieval.vector_search import VectorSearchEngine
from src.retrieval.hybrid_search import HybridSearchEngine
from src.retrieval.reranker import Reranker
from src.utils.logger import log
from src.utils.config import get_settings

class RetrievalService:
    """
    Retrieval Service
    =================
    Handles vector-based similarity scoring and hybrid document retrieval.
    """

    def __init__(
        self,
        vector_search: VectorSearchEngine,
        hybrid_search: HybridSearchEngine,
        reranker: Reranker
    ):
        self.vector_search = vector_search
        self.hybrid_search = hybrid_search
        self.reranker = reranker

    def retrieve_and_score(
        self,
        query: str,
        top_k: int
    ) -> Tuple[List[Document], float]:
        """
        Retrieves candidate documents for a query and calculates the maximum similarity score.

        Bypasses hybrid search and reranking if similarity score is below the threshold.
        """
        settings = get_settings()
        threshold = settings.rag_threshold

        log.debug("RetrievalService: retrieving and scoring for query='{}'", query[:80])

        # 1. Calculate similarity score from vector database
        scored_results = self.vector_search.search_with_scores(query, top_k=top_k)
        
        if not scored_results:
            log.warning("RetrievalService: no results found in vector search.")
            return [], 0.0

        max_similarity_score = float(scored_results[0][1])
        log.info("RetrievalService: calculated max similarity score = {:.4f}", max_similarity_score)

        # If similarity score is below threshold, bypass hybrid search and reranking
        if max_similarity_score < threshold:
            log.info(
                "RetrievalService: Similarity score {:.4f} < threshold {:.4f}. Bypassing Hybrid Search and Reranking.",
                max_similarity_score,
                threshold
            )
            return [], max_similarity_score

        # 2. Get hybrid search candidates
        candidates = self.hybrid_search.search(query, top_k=settings.hybrid_search_top_k)

        # 3. Rerank the hybrid search results to refine relevance
        reranked = self.reranker.rerank(query, candidates, top_k=settings.rerank_top_k)

        return reranked, max_similarity_score
