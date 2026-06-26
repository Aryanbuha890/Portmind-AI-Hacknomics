import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

from src.services.retrieval_service import RetrievalService
from src.services.relevance_checker import RelevanceChecker
from src.services.groq_fallback import GroqFallbackService
from src.services.response_generator import ResponseGenerator
from src.services.hybrid_rag_system import HybridRAGSystem
from src.utils.config import Settings


# =========================================================================
# Unit Tests for RetrievalService
# =========================================================================
class TestRetrievalService:
    @patch("src.services.retrieval_service.get_settings")
    def test_retrieve_and_score_success(self, mock_get_settings):
        # Arrange
        mock_settings = MagicMock()
        mock_settings.rag_threshold = 0.65
        mock_settings.hybrid_search_top_k = 5
        mock_settings.rerank_top_k = 3
        mock_get_settings.return_value = mock_settings

        mock_doc = Document(page_content="Port safety guidelines require hard hats.", metadata={"source_file": "safety.pdf"})
        
        mock_vector_search = MagicMock()
        mock_vector_search.search_with_scores.return_value = [(mock_doc, 0.85)]
        
        mock_hybrid_search = MagicMock()
        mock_hybrid_search.search.return_value = [mock_doc]
        
        mock_reranker = MagicMock()
        mock_reranker.rerank.return_value = [mock_doc]
        
        service = RetrievalService(
            vector_search=mock_vector_search,
            hybrid_search=mock_hybrid_search,
            reranker=mock_reranker
        )
        
        # Act
        docs, max_score = service.retrieve_and_score("crane safety helmets", top_k=5)
        
        # Assert
        assert len(docs) == 1
        assert docs[0].page_content == "Port safety guidelines require hard hats."
        assert max_score == 0.85
        mock_vector_search.search_with_scores.assert_called_once_with("crane safety helmets", top_k=5)
        mock_hybrid_search.search.assert_called_once_with("crane safety helmets", top_k=5)
        mock_reranker.rerank.assert_called_once_with("crane safety helmets", [mock_doc], top_k=3)

    @patch("src.services.retrieval_service.get_settings")
    def test_retrieve_and_score_empty(self, mock_get_settings):
        # Arrange
        mock_settings = MagicMock()
        mock_settings.rag_threshold = 0.65
        mock_get_settings.return_value = mock_settings

        mock_vector_search = MagicMock()
        mock_vector_search.search_with_scores.return_value = []
        
        mock_hybrid_search = MagicMock()
        mock_reranker = MagicMock()
        
        service = RetrievalService(
            vector_search=mock_vector_search,
            hybrid_search=mock_hybrid_search,
            reranker=mock_reranker
        )
        
        # Act
        docs, max_score = service.retrieve_and_score("nonexistent query", top_k=5)
        
        # Assert
        assert len(docs) == 0
        assert max_score == 0.0
        mock_vector_search.search_with_scores.assert_called_once_with("nonexistent query", top_k=5)
        mock_hybrid_search.search.assert_not_called()
        mock_reranker.rerank.assert_not_called()


# =========================================================================
# Unit Tests for RelevanceChecker
# =========================================================================
class TestRelevanceChecker:
    def test_is_context_sufficient_yes(self):
        # Arrange
        mock_groq_client = MagicMock()
        
        checker = RelevanceChecker(groq_client=mock_groq_client)
        docs = [Document(page_content="Use water on Class A fires.", metadata={"source_file": "fire.pdf"})]
        
        # Act
        result = checker.is_context_sufficient("how to put out class A fires", docs)
        
        # Assert
        assert result is True

    def test_is_context_sufficient_no(self):
        # Arrange
        mock_groq_client = MagicMock()
        
        checker = RelevanceChecker(groq_client=mock_groq_client)
        docs = []
        
        # Act
        result = checker.is_context_sufficient("crane lift regulations", docs)
        
        # Assert
        assert result is False


# =========================================================================
# Unit Tests for GroqFallbackService
# =========================================================================
class TestGroqFallbackService:
    def test_generate_general_answer(self):
        # Arrange
        mock_response = MagicMock()
        mock_response.content = "This is a general knowledge answer about cranes."
        
        mock_groq_client = MagicMock()
        mock_groq_client._llm.invoke.return_value = mock_response

        fallback = GroqFallbackService(groq_client=mock_groq_client)
        
        # Act
        answer = fallback.generate_general_answer("What is the function of a harbor crane?")
        
        # Assert
        assert answer == "This is a general knowledge answer about cranes."
        mock_groq_client._llm.invoke.assert_called_once()


# =========================================================================
# Unit Tests for ResponseGenerator
# =========================================================================
class TestResponseGenerator:
    def test_generate_rag_response(self):
        # Arrange
        mock_groq_client = MagicMock()
        mock_groq_client.generate_answer.return_value = {
            "answer": "Answer from doc.",
            "sources": ["safety.pdf"],
            "confidence": "High"
        }
        
        mock_fallback = MagicMock()
        generator = ResponseGenerator(groq_client=mock_groq_client, fallback_service=mock_fallback)
        docs = [Document(page_content="doc content")]
        
        # Act
        res = generator.generate_rag_response("question", docs, similarity_score=0.75)
        
        # Assert
        assert res["answer"] == "Answer from doc."
        assert res["source"] == "RAG"
        assert res["confidence"] == "High"
        assert res["sources"] == ["safety.pdf"]

    def test_generate_fallback_response(self):
        # Arrange
        mock_groq_client = MagicMock()
        mock_fallback = MagicMock()
        mock_fallback.generate_general_answer.return_value = "General AI response."
        
        generator = ResponseGenerator(groq_client=mock_groq_client, fallback_service=mock_fallback)
        
        # Act
        res = generator.generate_fallback_response("question", similarity_score=0.25)
        
        # Assert
        assert res["answer"] == "General AI response."
        assert res["source"] == "Groq"
        assert res["confidence"] == "Low"
        assert res["sources"] == []


class TestHybridRAGSystem:
    @patch("src.services.hybrid_rag_system.get_settings")
    def test_answer_question_rag_flow(self, mock_get_settings):
        # Arrange
        mock_settings = MagicMock(spec=Settings)
        mock_settings.rag_threshold = 0.65
        mock_settings.vector_search_top_k = 5
        mock_settings.hybrid_search_top_k = 5
        mock_settings.rerank_top_k = 3
        mock_get_settings.return_value = mock_settings

        # Mock subservices
        mock_retrieval = MagicMock(spec=RetrievalService)
        mock_doc = Document(page_content="RAG context", metadata={"source_file": "safety.pdf"})
        
        # We mock vector_search, hybrid_search, and reranker attributes on RetrievalService
        mock_retrieval.vector_search = MagicMock()
        mock_retrieval.vector_search.search_with_scores.return_value = [(mock_doc, 0.85)]
        mock_retrieval.hybrid_search = MagicMock()
        mock_retrieval.hybrid_search.search.return_value = [mock_doc]
        mock_retrieval.reranker = MagicMock()
        mock_retrieval.reranker.rerank.return_value = [mock_doc]

        mock_relevance = MagicMock(spec=RelevanceChecker)
        mock_generator = MagicMock(spec=ResponseGenerator)
        mock_generator.generate_rag_response.return_value = {
            "answer": "Detailed safety answer."
        }

        system = HybridRAGSystem(
            retrieval_service=mock_retrieval,
            relevance_checker=mock_relevance,
            response_generator=mock_generator
        )

        # Act
        response = system.answer_question("is safety gear mandatory?")

        # Assert
        assert response["answer"] == "Detailed safety answer."
        assert response["source"] == "RAG"
        assert response["sources"] == []
        assert response["confidence"] == "Medium"
        
        mock_retrieval.vector_search.search_with_scores.assert_called_once()
        mock_retrieval.hybrid_search.search.assert_called_once()
        mock_retrieval.reranker.rerank.assert_called_once()
        mock_generator.generate_rag_response.assert_called_once()
        mock_generator.generate_fallback_response.assert_not_called()

    @patch("src.services.hybrid_rag_system.get_settings")
    def test_answer_question_fallback_due_to_threshold(self, mock_get_settings):
        # Arrange
        mock_settings = MagicMock(spec=Settings)
        mock_settings.rag_threshold = 0.65
        mock_settings.vector_search_top_k = 5
        mock_get_settings.return_value = mock_settings

        mock_retrieval = MagicMock(spec=RetrievalService)
        mock_retrieval.vector_search = MagicMock()
        mock_retrieval.vector_search.search_with_scores.return_value = [(Document(page_content="Unrelated stuff"), 0.25)]

        mock_relevance = MagicMock(spec=RelevanceChecker)
        mock_generator = MagicMock(spec=ResponseGenerator)
        mock_generator.generate_fallback_response.return_value = {
            "answer": "General Groq answer."
        }

        system = HybridRAGSystem(
            retrieval_service=mock_retrieval,
            relevance_checker=mock_relevance,
            response_generator=mock_generator
        )

        # Act
        response = system.answer_question("what is the weather?")

        # Assert
        assert response["answer"] == "General Groq answer."
        assert response["source"] == "Groq"
        
        mock_retrieval.vector_search.search_with_scores.assert_called_once()
        mock_generator.generate_rag_response.assert_not_called()
        mock_generator.generate_fallback_response.assert_called_once_with(
            question="what is the weather?",
            similarity_score=0.25,
            system_prompt=None
        )
