from typing import Dict, Any, Optional
import time
from src.services.retrieval_service import RetrievalService
from src.services.relevance_checker import RelevanceChecker
from src.services.response_generator import ResponseGenerator
from src.utils.config import get_settings
from src.utils.logger import log

class HybridRAGSystem:
    """
    Hybrid RAG System Orchestrator
    ==============================
    Coordinates dense scored retrieval, similarity threshold check,
    and response generation (RAG or Gemini fallback). Bypasses relevance checking
    and hybrid/reranking search where appropriate for optimal speed.
    """

    def __init__(
        self,
        retrieval_service: RetrievalService,
        relevance_checker: RelevanceChecker,
        response_generator: ResponseGenerator
    ):
        self.retrieval_service = retrieval_service
        self.relevance_checker = relevance_checker
        self.response_generator = response_generator
        self.settings = get_settings()

    def answer_question(
        self,
        question: str,
        agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate the answer generation flow:
        1. Retrieve top-k documents and calculate similarity score.
        2. Evaluate similarity score against configured threshold.
        3. If >= threshold, generate RAG response.
        4. Else, generate Gemini fallback response.
        """
        # Load the configuration threshold
        threshold = getattr(self.settings, "rag_threshold", 0.65)
        log.info("------------------------------------------------------------")
        log.info("Processing Query: '{}'", question)
        log.info("RAG Threshold Configured: {}", threshold)

        start_time = time.time()
        retrieval_time = 0.0
        reranking_time = 0.0
        generation_time = 0.0

        documents = []
        similarity_score = 0.0
        retrieval_success = False

        # Resolve specialized agent prompt if requested
        system_prompt = None
        if agent:
            from src.llm.prompts import get_agent_system_prompt
            try:
                system_prompt = get_agent_system_prompt(agent)
                log.info("Applying specialized agent prompt for: '{}'", agent)
            except ValueError as e:
                log.warning("Specialized agent prompt could not be resolved for '{}': {}", agent, e)

        # 1. Retrieval (Similarity score calculation via Vector Search)
        retrieval_start = time.time()
        try:
            scored_results = self.retrieval_service.vector_search.search_with_scores(
                question, top_k=self.settings.vector_search_top_k
            )
            retrieval_time = time.time() - retrieval_start
            
            if scored_results:
                similarity_score = float(scored_results[0][1])
            else:
                similarity_score = 0.0
            retrieval_success = True
            log.info("Calculated Similarity Score: {:.4f}", similarity_score)
        except Exception as exc:
            retrieval_time = time.time() - retrieval_start
            log.exception("Retrieval failed. Will fallback to Groq. Error: {}", exc)
            similarity_score = 0.0
            retrieval_success = False

        # 2. Similarity threshold check
        if retrieval_success and similarity_score >= threshold:
            log.info("Similarity score {:.4f} >= threshold {:.4f}. Performing RAG route...", similarity_score, threshold)
            
            # 3. Hybrid search and Reranking (Reranking stage)
            reranking_start = time.time()
            try:
                candidates = self.retrieval_service.hybrid_search.search(
                    question, top_k=self.settings.hybrid_search_top_k
                )
                documents = self.retrieval_service.reranker.rerank(
                    question, candidates, top_k=self.settings.rerank_top_k
                )
                reranking_time = time.time() - reranking_start
            except Exception as exc:
                reranking_time = time.time() - reranking_start
                log.exception("Reranking failed. Will fallback to Groq. Error: {}", exc)
                documents = []

            if documents:
                # 4. Generate RAG Answer (Generation stage)
                generation_start = time.time()
                try:
                    response_dict = self.response_generator.generate_rag_response(
                        question=question,
                        documents=documents,
                        similarity_score=similarity_score,
                        system_prompt=system_prompt
                    )
                    generation_time = time.time() - generation_start
                    total_time = time.time() - start_time
                    
                    # Log internally: retrieval time, reranking time, generation time, total request time
                    log.info("Retrieval: {:.1f}s", retrieval_time)
                    log.info("Reranking: {:.1f}s", reranking_time)
                    log.info("Generation: {:.1f}s", generation_time)
                    log.info("Total: {:.1f}s", total_time)
                    log.info("Final Source Used: RAG")
                    log.info("------------------------------------------------------------")
                    
                    return {
                        "answer": response_dict["answer"],
                        "sources": response_dict.get("sources", []),
                        "confidence": response_dict.get("confidence", "Medium"),
                        "source": response_dict.get("source", "RAG"),
                    }
                except Exception as exc:
                    generation_time = time.time() - generation_start
                    total_time = time.time() - start_time
                    
                    # Check for Groq 429 error
                    exc_str = str(exc).upper()
                    if "429" in str(exc) or "RESOURCE_EXHAUSTED" in exc_str or "QUOTA" in exc_str:
                        log.exception("RAG generation failed with 429/Quota error: {}", exc)
                        return {"answer": "General AI service is currently unavailable. Please try again later."}
                    
                    log.exception("RAG generation failed. Falling back to Groq. Error: {}", exc)
            else:
                log.info("Retrieved context is empty. Falling back to Groq.")
        else:
            if retrieval_success:
                log.info("Retrieval Decision: Similarity check FAILED (score {:.4f} < threshold {:.4f}).", similarity_score, threshold)
            else:
                log.info("Retrieval Decision: FAILED (retrieval error).")

        # 5. Groq fallback answer generation (Generation stage)
        generation_start = time.time()
        try:
            response_dict = self.response_generator.generate_fallback_response(
                question=question,
                similarity_score=similarity_score,
                system_prompt=system_prompt
            )
            generation_time = time.time() - generation_start
            total_time = time.time() - start_time
            
            # Log internally: retrieval time, reranking time, generation time, total request time
            log.info("Retrieval: {:.1f}s", retrieval_time)
            log.info("Reranking: {:.1f}s", reranking_time)
            log.info("Generation: {:.1f}s", generation_time)
            log.info("Total: {:.1f}s", total_time)
            log.info("Final Source Used: Groq")
            log.info("------------------------------------------------------------")
            
            return {
                "answer": response_dict["answer"],
                "sources": response_dict.get("sources", []),
                "confidence": response_dict.get("confidence", "Medium"),
                "source": response_dict.get("source", "Groq"),
            }
        except Exception as exc:
            generation_time = time.time() - generation_start
            total_time = time.time() - start_time
            
            # Log timings on error too
            log.info("Retrieval: {:.1f}s", retrieval_time)
            log.info("Reranking: {:.1f}s", reranking_time)
            log.info("Generation: {:.1f}s", generation_time)
            log.info("Total: {:.1f}s", total_time)
            
            # Check for Gemini 429 error
            exc_str = str(exc).upper()
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in exc_str or "QUOTA" in exc_str:
                log.exception("Fallback generation failed with 429/Quota error: {}", exc)
                return {"answer": "General AI service is currently unavailable. Please try again later."}
            
            log.error("Groq Fallback Generation failed: {}", exc)
            log.info("------------------------------------------------------------")
            return {"answer": "I apologize, but I encountered an error while processing your request. Please try again later."}
