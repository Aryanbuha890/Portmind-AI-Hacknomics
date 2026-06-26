# 🚢 Maritime-RAG

**Hybrid Retrieval-Augmented Generation for Maritime Safety & Port Operations**

A production-ready RAG system that combines dense vector search with sparse keyword retrieval (BM25), cross-encoder reranking, and Google Gemini 2.5 Flash to answer maritime safety questions with source citations and confidence scoring.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [API Reference](#-api-reference)
- [Agent System](#-agent-system)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Contributing](#-contributing)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Multi-PDF Ingestion** | Load and process multiple maritime safety PDFs |
| **Smart Chunking** | 512-char chunks with 50-char overlap using recursive splitting |
| **Dense Embeddings** | BAAI/bge-small-en-v1.5 (384-dim, normalised) |
| **Hybrid Retrieval** | Vector similarity + BM25 keyword search fused via RRF |
| **Cross-Encoder Reranking** | BAAI/bge-reranker-large for precision refinement |
| **Gemini 2.5 Flash** | Fast, high-quality answer generation |
| **Source Citations** | Every answer cites the originating PDF documents |
| **Confidence Scoring** | High / Medium / Low confidence assessment |
| **Specialised Agents** | Chemical Leak, Crane Safety, Vessel Safety, Emergency Response |
| **REST API** | FastAPI with Swagger docs at `/docs` |

---

## 🏗️ Architecture

```
                    ┌─────────────┐
                    │   User      │
                    │   Query     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  FastAPI    │
                    │  Endpoint   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │                         │
       ┌──────▼──────┐          ┌──────▼──────┐
       │   Vector    │          │    BM25     │
       │   Search    │          │   Keyword   │
       │  (ChromaDB) │          │   Search    │
       └──────┬──────┘          └──────┬──────┘
              │                         │
              └────────────┬────────────┘
                           │
                    ┌──────▼──────┐
                    │ Reciprocal  │
                    │ Rank Fusion │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Reranker   │
                    │(BGE-large)  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Gemini    │
                    │  2.5 Flash  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Structured │
                    │  Response   │
                    └─────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| Framework | LangChain |
| Vector Store | ChromaDB |
| Embeddings | BAAI/bge-small-en-v1.5 |
| Reranker | BAAI/bge-reranker-large |
| LLM | Google Gemini 2.5 Flash |
| API | FastAPI + Uvicorn |
| Keyword Search | BM25 (rank-bm25) |
| Logging | Loguru |
| Config | Pydantic Settings |

---

## 📁 Project Structure

```
maritime-rag/
│
├── data/
│   ├── raw_pdfs/          # Place your PDF documents here
│   └── processed/         # Auto-generated processed data
│
├── chroma_db/             # ChromaDB vector persistence
│
├── src/
│   ├── ingestion/
│   │   ├── pdf_loader.py      # Multi-PDF loading with metadata
│   │   ├── text_splitter.py   # Recursive chunking (512/50)
│   │   └── embedder.py        # BGE embeddings + ChromaDB storage
│   │
│   ├── retrieval/
│   │   ├── vector_search.py   # Dense similarity search
│   │   ├── hybrid_search.py   # Vector + BM25 with RRF fusion
│   │   └── reranker.py        # Cross-encoder reranking
│   │
│   ├── llm/
│   │   ├── gemini_client.py   # Gemini 2.5 Flash integration
│   │   └── prompts.py         # System & agent prompt templates
│   │
│   ├── api/
│   │   └── app.py             # FastAPI endpoints
│   │
│   ├── utils/
│   │   ├── config.py          # Pydantic settings from .env
│   │   └── logger.py          # Loguru structured logging
│   │
│   └── main.py               # CLI entry point
│
├── notebooks/             # Jupyter notebooks for exploration
├── tests/                 # Pytest test suite
├── .env.example           # Environment template
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── .gitignore
```

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd RAG

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your-actual-api-key
```

### 3. Add Documents

Place your maritime safety PDF documents in `data/raw_pdfs/`:

```
data/raw_pdfs/
├── IMDG_Code.pdf
├── SOLAS_Convention.pdf
├── OSHA_Maritime_Standards.pdf
└── Port_Emergency_Plan.pdf
```

### 4. Ingest Documents

```bash
python -m src.main ingest
```

### 5. Start the API Server

```bash
python -m src.main serve
```

The API will be available at `http://localhost:8000` with Swagger docs at `http://localhost:8000/docs`.

### 6. Ask a Question

```bash
# Via CLI
python -m src.main query "What is the procedure after chemical leakage?"

# Via API
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the procedure after chemical leakage?"}'
```

---

## 📡 API Reference

### `POST /ask`

Ask a maritime safety question.

**Request:**
```json
{
  "question": "What is the procedure after chemical leakage?",
  "agent": null
}
```

**Response:**
```json
{
  "answer": "According to the IMDG Code, after a chemical leakage the following steps must be taken: 1) Alert the ship's master...",
  "sources": ["IMDG.pdf", "OSHA.pdf"],
  "confidence": "High"
}
```

### `POST /ask/{agent_name}`

Ask via a specialised agent (`chemical_leak`, `crane_safety`, `vessel_safety`, `emergency_response`).

### `POST /ingest`

Trigger PDF ingestion from `data/raw_pdfs/`.

**Response:**
```json
{
  "message": "Successfully ingested 4 document(s)",
  "documents_loaded": 45,
  "chunks_created": 312
}
```

### `GET /health`

System health check.

### `GET /stats`

Vector store statistics and available PDFs.

---

## 🤖 Agent System

The system supports **specialised agents** for domain-specific expertise:

| Agent | Endpoint | Focus |
|-------|----------|-------|
| Chemical Leak | `/ask/chemical_leak` | IMDG Code, spill response, PPE, decontamination |
| Crane Safety | `/ask/crane_safety` | Load calculations, inspections, wind limits |
| Vessel Safety | `/ask/vessel_safety` | SOLAS, berthing, fire safety, ballast water |
| Emergency Response | `/ask/emergency_response` | Evacuation, rescue, fire/explosion, comms |

Each agent uses a tailored system prompt to focus the LLM on its domain while using the same retrieval pipeline.

### Adding a Custom Agent

1. Add a new prompt template in `src/llm/prompts.py`
2. Register it in the `AGENT_PROMPTS` dictionary
3. Access via `/ask/your_agent_name`

---

## ⚙️ Configuration

All settings are managed via `.env` file. Key parameters:

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Google Gemini API key (required) |
| `EMBEDDING_MODEL` | BAAI/bge-small-en-v1.5 | HuggingFace embedding model |
| `RERANKER_MODEL` | BAAI/bge-reranker-large | Cross-encoder reranker |
| `CHUNK_SIZE` | 512 | Characters per chunk |
| `CHUNK_OVERLAP` | 50 | Overlap between chunks |
| `VECTOR_SEARCH_TOP_K` | 10 | Vector search candidates |
| `RERANK_TOP_K` | 5 | Results after reranking |
| `LLM_TEMPERATURE` | 0.3 | Gemini sampling temperature |
| `API_PORT` | 8000 | FastAPI server port |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src

# Run specific test class
pytest tests/test_maritime_rag.py::TestTextSplitter -v
```

---

## 📄 License

This project is for educational and research purposes.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

Built with ❤️ for Maritime Safety
