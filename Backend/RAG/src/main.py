"""
Maritime-RAG – Main Entry Point
================================
CLI interface to run ingestion, query, or start the API server.

Usage:
    python -m src.main ingest          # Ingest PDFs from data/raw_pdfs/
    python -m src.main query "question" # Run a one-off query
    python -m src.main serve           # Start the FastAPI server
"""

import sys
import argparse

import uvicorn

from src.utils.logger import log
from src.utils.config import get_settings
from src.ingestion.pdf_loader import PDFDocumentLoader
from src.ingestion.text_splitter import DocumentSplitter
from src.ingestion.embedder import DocumentEmbedder
from src.retrieval.hybrid_search import HybridSearchEngine
from src.retrieval.reranker import Reranker
from src.retrieval.vector_search import VectorSearchEngine
from src.llm.groq_client import GroqClient
from src.services import (
    RetrievalService,
    RelevanceChecker,
    GroqFallbackService,
    ResponseGenerator,
    HybridRAGSystem,
)


def run_ingestion() -> None:
    """
    Full ingestion pipeline:
        1. Load all PDFs from data/raw_pdfs/
        2. Split into chunks (512 chars, 50 overlap)
        3. Embed with BGE-small-en-v1.5
        4. Persist to ChromaDB
    """
    log.info("=" * 60)
    log.info("STARTING INGESTION PIPELINE")
    log.info("=" * 60)

    loader = PDFDocumentLoader()
    splitter = DocumentSplitter()
    embedder = DocumentEmbedder()

    # Step 1: Load
    documents = loader.load_directory()
    if not documents:
        log.warning("No documents to ingest. Add PDFs to data/raw_pdfs/ and retry.")
        return

    # Step 2: Split
    chunks = splitter.split(documents)
    log.info("Created {} chunks from {} document pages", len(chunks), len(documents))

    # Step 3: Embed & Store
    vectorstore = embedder.embed_and_store(chunks)
    count = vectorstore._collection.count()
    log.info("ChromaDB now contains {} vectors", count)

    log.info("=" * 60)
    log.info("INGESTION COMPLETE")
    log.info("=" * 60)


def run_query(question: str) -> None:
    """
    One-shot query pipeline:
        Uses Hybrid RAG + Gemini fallback and LLM relevance checking.
    """
    log.info("=" * 60)
    log.info("QUERY: {}", question)
    log.info("=" * 60)

    vector_search = VectorSearchEngine()
    search_engine = HybridSearchEngine()
    reranker = Reranker()
    llm = GroqClient()

    # Setup services
    retrieval_service = RetrievalService(
        vector_search=vector_search,
        hybrid_search=search_engine,
        reranker=reranker
    )
    relevance_checker = RelevanceChecker(groq_client=llm)
    fallback_service = GroqFallbackService(groq_client=llm)
    response_generator = ResponseGenerator(groq_client=llm, fallback_service=fallback_service)

    hybrid_rag = HybridRAGSystem(
        retrieval_service=retrieval_service,
        relevance_checker=relevance_checker,
        response_generator=response_generator
    )

    # Execute Hybrid RAG System
    result = hybrid_rag.answer_question(question=question)

    # Display
    print("\n" + "=" * 60)
    print(f"📝 Answer:\n{result['answer']}")
    print(f"\n⚡ Source: {result['source']}")
    print(f"📚 Sources Cited: {', '.join(result['sources']) if result['sources'] else 'None'}")
    print(f"🎯 Confidence: {result['confidence']:.4f}")
    print("=" * 60 + "\n")


def run_server() -> None:
    """Start the FastAPI server with uvicorn."""
    settings = get_settings()
    log.info(
        "Starting API server on {}:{}",
        settings.api_host,
        settings.api_port,
    )
    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="maritime-rag",
        description="Maritime Safety Hybrid RAG System",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- ingest ---
    subparsers.add_parser("ingest", help="Ingest PDFs from data/raw_pdfs/")

    # --- query ---
    query_parser = subparsers.add_parser("query", help="Ask a question")
    query_parser.add_argument("question", type=str, help="Your maritime safety question")

    # --- serve ---
    subparsers.add_parser("serve", help="Start the FastAPI server")

    args = parser.parse_args()

    if args.command == "ingest":
        run_ingestion()
    elif args.command == "query":
        run_query(args.question)
    elif args.command == "serve":
        run_server()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
