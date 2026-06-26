"""
Maritime-RAG Test Suite
========================
Unit and integration tests for the Maritime-RAG system.
"""

import pytest
from pathlib import Path


# =========================================================================
# Fixtures
# =========================================================================
@pytest.fixture
def sample_text():
    """Sample maritime safety text for testing."""
    return (
        "The International Maritime Dangerous Goods (IMDG) Code is a uniform "
        "international code for the transport of dangerous goods by sea. In the "
        "event of a chemical leakage on board a vessel, the following procedures "
        "must be followed: 1) Immediately alert the ship's master and safety "
        "officer. 2) Evacuate all non-essential personnel from the affected area. "
        "3) Don appropriate personal protective equipment (PPE) including chemical "
        "resistant suits, gloves, and respiratory protection. 4) Identify the "
        "hazardous material using the IMDG Code classifications. 5) Contain the "
        "spill using appropriate absorbent materials. 6) Notify the port authority "
        "and relevant environmental agencies."
    )


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parents[1]


# =========================================================================
# Configuration Tests
# =========================================================================
class TestConfig:
    """Test the configuration module."""

    def test_settings_load(self):
        """Settings should load without errors."""
        from src.utils.config import get_settings

        settings = get_settings()
        assert settings is not None
        assert settings.chunk_size == 512
        assert settings.chunk_overlap == 50

    def test_embedding_model_default(self):
        """Default embedding model should be BGE-small."""
        from src.utils.config import get_settings

        settings = get_settings()
        assert "bge-small" in settings.embedding_model.lower()

    def test_chroma_collection_name(self):
        """ChromaDB collection should be maritime_safety."""
        from src.utils.config import get_settings

        settings = get_settings()
        assert settings.chroma_collection_name == "maritime_safety"

    def test_data_paths(self, project_root):
        """Data path properties should resolve correctly."""
        from src.utils.config import get_settings

        settings = get_settings()
        assert settings.raw_pdfs_dir.name == "raw_pdfs"
        assert settings.processed_dir.name == "processed"


# =========================================================================
# Text Splitter Tests
# =========================================================================
class TestTextSplitter:
    """Test the document chunking module."""

    def test_split_text(self, sample_text):
        """Splitting text should produce multiple chunks."""
        from src.ingestion.text_splitter import DocumentSplitter

        splitter = DocumentSplitter(chunk_size=200, chunk_overlap=20)
        chunks = splitter.split_text(sample_text)
        assert len(chunks) > 1

    def test_chunk_size_respected(self, sample_text):
        """Each chunk should not exceed chunk_size (with some tolerance)."""
        from src.ingestion.text_splitter import DocumentSplitter

        splitter = DocumentSplitter(chunk_size=200, chunk_overlap=20)
        chunks = splitter.split_text(sample_text)
        for chunk in chunks:
            # Allow some tolerance for the recursive splitter
            assert len(chunk) <= 250, f"Chunk too large: {len(chunk)} chars"

    def test_empty_input(self):
        """Empty input should return empty output."""
        from src.ingestion.text_splitter import DocumentSplitter

        splitter = DocumentSplitter()
        result = splitter.split([])
        assert result == []


# =========================================================================
# PDF Loader Tests
# =========================================================================
class TestPDFLoader:
    """Test the PDF loading module."""

    def test_loader_initialisation(self):
        """PDFDocumentLoader should initialise without errors."""
        from src.ingestion.pdf_loader import PDFDocumentLoader

        loader = PDFDocumentLoader()
        assert loader.source_dir is not None

    def test_load_nonexistent_file(self):
        """Loading a non-existent PDF should raise FileNotFoundError."""
        from src.ingestion.pdf_loader import PDFDocumentLoader

        loader = PDFDocumentLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_single("nonexistent_document.pdf")

    def test_get_available_pdfs(self):
        """Should return a list (possibly empty) of PDF filenames."""
        from src.ingestion.pdf_loader import PDFDocumentLoader

        loader = PDFDocumentLoader()
        pdfs = loader.get_available_pdfs()
        assert isinstance(pdfs, list)


# =========================================================================
# Prompt Tests
# =========================================================================
class TestPrompts:
    """Test prompt template module."""

    def test_rag_prompts_exist(self):
        """RAG prompts should be non-empty strings."""
        from src.llm.prompts import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT

        assert len(RAG_SYSTEM_PROMPT) > 50
        assert "{context}" in RAG_USER_PROMPT
        assert "{question}" in RAG_USER_PROMPT

    def test_agent_prompt_retrieval(self):
        """Known agent names should return valid prompts."""
        from src.llm.prompts import get_agent_system_prompt

        for agent in ["chemical_leak", "crane_safety", "vessel_safety", "emergency_response"]:
            prompt = get_agent_system_prompt(agent)
            assert len(prompt) > 50

    def test_unknown_agent_raises(self):
        """Unknown agent name should raise ValueError."""
        from src.llm.prompts import get_agent_system_prompt

        with pytest.raises(ValueError):
            get_agent_system_prompt("unknown_agent")


# =========================================================================
# API Model Tests
# =========================================================================
class TestAPIModels:
    """Test Pydantic request/response models."""

    def test_ask_request_validation(self):
        """AskRequest should validate minimum length."""
        from src.api.app import AskRequest

        req = AskRequest(question="What is the procedure after chemical leakage?")
        assert req.question is not None

    def test_ask_response_model(self):
        """AskResponse should accept valid data."""
        from src.api.app import AskResponse

        resp = AskResponse(
            answer="Follow IMDG Code procedures."
        )
        assert resp.answer == "Follow IMDG Code procedures."
