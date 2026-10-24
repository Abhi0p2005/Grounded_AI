# GroundedAI

> A domain-agnostic, config-driven knowledge copilot platform with RAG, citations, and safety guardrails.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 What is GroundedAI?

GroundedAI is a **Retrieval-Augmented Generation (RAG)** platform that turns document collections into safe, cited, measurable chat assistants. Drop in a company's documents, configure guardrails, and get answers that are:

- ✅ **Grounded in sources** - Every answer cites specific document chunks
- ✅ **Safe by design** - PII masked, prompt injection blocked, confidence thresholds
- ✅ **Domain-agnostic** - Same engine, any industry (finance, HR, legal, etc.)
- ✅ **Config-driven** - New workspace = YAML files, zero code changes

---

## 🚀 Key Features

### 🔍 Retrieval-Augmented Generation (RAG)
- **Vector search** with pgvector (cosine similarity)
- **Citation verification** - Only cite chunks that were actually retrieved
- **Confidence thresholding** - Refuse to answer when similarity is too low
- **Workspace isolation** - SQL-enforced separation between document collections

### 🛡️ Safety & Guardrails
- **PII masking** - Automatic redaction of phone numbers, emails, PAN, Aadhaar, card numbers
- **Input guardrails** - Block harmful topics, detect prompt injection attempts
- **Output guardrails** - Forbidden phrase detection, citation requirement enforcement
- **Graceful degradation** - System works even if LLM is unavailable

### 🏗️ Architecture
- **Multi-workspace** - One platform, multiple isolated knowledge bases
- **Config-driven** - Workspace = folder with YAML configs + documents
- **Pluggable LLM** - Currently Google Gemini, easily swappable
- **Local embeddings** - sentence-transformers (no external API dependency)

---

## 📸 Demo (Current MVP)

```bash
# Ask a question
curl -X POST http://localhost:8000/api/workspaces/finance-demo/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is interest rate?", "history": []}'

# Response with citations
{
  "answer": "An interest rate is the percentage charged on a loan amount or paid on savings. It represents the cost of borrowing money or the return on invested funds.",
  "refused": false,
  "route": "knowledge",
  "citations": [
    {
      "chunk_id": 1,
      "document": "finance_basics.pdf",
      "page": 1,
      "score": 0.78,
      "snippet": "An interest rate is the percentage charged on a loan amount..."
    }
  ],
  "flags": [],
  "latency_ms": 1850
}
```

---

## 🏁 Quick Start (5 minutes)

### Prerequisites
- **Docker Desktop** (running)
- **Python 3.11+**
- **Google AI Studio API Key** ([Get one free](https://aistudio.google.com/))

### 1. Clone & Setup

```bash
git clone https://github.com/Abhi0p2005/Grounded_AI.git
cd Grounded_AI

# Add your API key
cp .env.example .env
# Edit .env and add: GOOGLE_API_KEY=your_actual_key_here

# Install dependencies
cd backend
pip install -r ../requirements.txt
```

### 2. Start Infrastructure

```bash
# Start PostgreSQL + Redis
docker compose up -d db redis

# Wait ~30 seconds for services to be healthy
docker compose ps
```

### 3. Start Backend

```bash
# From backend/ directory
uvicorn app.main:app --reload
```

Backend runs at: http://localhost:8000

### 4. Load Workspace & Ingest Documents

```bash
# In a new terminal, from project root

# Load workspace configuration
curl -X POST http://localhost:8000/api/workspaces/reload

# Ingest demo documents (3 dummy finance PDFs included)
python scripts/ingest.py --workspace finance-demo
```

### 5. Test Chat

```bash
curl -X POST http://localhost:8000/api/workspaces/finance-demo/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is EMI?", "history": []}'
```

**Interactive API Docs**: http://localhost:8000/docs

---

## 📁 Project Structure

```
groundedai/
├── backend/
│   ├── app/
│   │   ├── agent/          # RAG logic, prompts
│   │   ├── api/            # FastAPI endpoints
│   │   ├── core/           # LLM, embeddings, config
│   │   ├── ingestion/      # PDF parsing, chunking
│   │   ├── retrieval/      # Vector search
│   │   ├── guardrails/     # PII, safety rules
│   │   ├── tools/          # Tool registry (future)
│   │   └── evals/          # Evaluation harness (future)
│   ├── tests/              # Unit & integration tests
│   └── db/                 # SQL schema
├── workspaces/
│   └── finance-demo/
│       ├── workspace.yaml      # Main config
│       ├── guardrails.yaml     # Safety rules
│       ├── tools.yaml          # Tool definitions
│       ├── eval.yaml           # Test cases
│       ├── docs/               # PDFs (3 dummy files included)
│       └── SOURCES.md          # Document sources
├── scripts/
│   ├── ingest.py               # Document ingestion CLI
│   └── create_dummy_docs.py    # Generate test PDFs
├── docs/
│   └── DECISIONS.md            # Architecture decisions log
├── docker-compose.yml          # Infrastructure setup
├── TESTING.md                  # Comprehensive testing guide
└── README.md                   # This file
```

---

## 🧪 Testing

See [TESTING.md](TESTING.md) for comprehensive test cases including:

- ✅ Knowledge questions with citations
- ✅ Low-confidence refusals
- ✅ Blocked topic detection
- ✅ Prompt injection blocking
- ✅ PII masking
- ✅ Workspace isolation

---

## 🔧 Configuration

### Workspace Configuration (`workspace.yaml`)

```yaml
slug: finance-demo
name: Consumer Finance Assistant
description: Answers questions about consumer lending rules
assistant_persona: >
  You are a careful assistant. Answer only from the provided document excerpts.
retrieval:
  top_k: 5
  min_score: 0.35  # Confidence threshold
  hybrid: false
llm:
  model: gemini-1.5-flash
  temperature: 0.1
  max_tokens: 700
history_turns: 4
```

### Guardrails Configuration (`guardrails.yaml`)

```yaml
pii:
  enabled: true
  patterns:
    phone_in: '(?<!\d)(?:\+91[\-\s]?)?[6-9]\d{9}(?!\d)'
    email: '[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}'
    pan: '\b[A-Z]{5}[0-9]{4}[A-Z]\b'

input:
  blocked_topics:
    - "investment advice"
    - "which stock should i buy"
  injection_heuristics:
    - '(?i)ignore (all|previous|above) instructions'

output:
  forbidden_phrases:
    - "guaranteed approval"
    - "100% approval"
  require_citation_for_knowledge: true
  llm_auditor: true
```

---

## 🏗️ How It Works

### Request Flow

```
User Question
    │
    ▼
[1] PII Masking (regex: phone, email, PAN, Aadhaar)
    │
    ▼
[2] Input Guardrails (blocked topics, injection detection)
    │
    ▼
[3] Vector Search (pgvector top-k, workspace-filtered)
    │
    ▼
[4] Confidence Check (score >= min_score?)
    │
    ▼
[5] LLM RAG Answer (with numbered excerpts)
    │
    ▼
[6] Citation Verification (strip invalid chunk IDs)
    │
    ▼
[7] Output Guardrails (forbidden phrases, citation presence)
    │
    ▼
Response with Citations
```

### Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Language | Python 3.11+ | Type hints everywhere |
| API | FastAPI + Uvicorn | Pydantic v2 validation |
| LLM | Google Gemini | `gemini-1.5-flash` (configurable) |
| Embeddings | sentence-transformers | `all-MiniLM-L6-v2` (384-dim, local) |
| Database | PostgreSQL 16 + pgvector | Vector similarity search |
| Cache | Redis 7 | Rate limiting, caching (future) |
| PDF Parsing | pypdf | Preserves page numbers |
| Testing | pytest | Unit + integration tests |

---

## 📊 Current Status

### ✅ Completed (Phase 0 + Phase 1)

- [x] Repository structure & configuration
- [x] Database schema with pgvector
- [x] Workspace config loader (YAML validation)
- [x] PDF parsing with page tracking
- [x] Token-aware chunking (500 tokens, 80 overlap)
- [x] Embedding model (sentence-transformers)
- [x] Ingestion pipeline (SHA256 deduplication)
- [x] Vector search with workspace isolation
- [x] Google Gemini LLM client (with retries)
- [x] Simple RAG with citation verification
- [x] PII masking (phone, email, PAN, Aadhaar, card)
- [x] Input guardrails (blocked topics, injection)
- [x] Output guardrails (forbidden phrases)
- [x] REST API (workspaces, documents, chat)
- [x] Dummy test documents (3 finance PDFs)

### 🚧 In Progress (Phase 2)

- [ ] Tool registry + built-in tools (EMI calculator, etc.)
- [ ] Full LangGraph agent with router
- [ ] LLM auditor with fallback
- [ ] Redis caching
- [ ] Query logging to database
- [ ] Second workspace (hr-demo)
- [ ] Evaluation harness (metrics, judge, report)
- [ ] Threshold tuning

### 📅 Planned (Phase 3)

- [ ] React + TypeScript frontend
- [ ] Chat UI with citation display
- [ ] Document upload interface
- [ ] Admin panel (logs, flags)
- [ ] Evaluation results UI
- [ ] Docker Compose full stack
- [ ] Polished documentation

---

## 🎓 Core Concepts

### Workspace
An isolated knowledge base with its own documents, chunks, tools, and guardrails. Identified by a slug (e.g., `finance-demo`). Retrieval **always** filters by workspace; there is no cross-workspace leakage.

### Chunk
A ~500-token slice of a document with overlap, plus metadata (document name, page number, chunk index). The unit of retrieval and citation. Each has a stable integer ID.

### Citation
A list of chunk IDs the answer relied on. Code verifies each cited ID was actually in the retrieved set; invalid citations are stripped and the answer is flagged.

### Confidence Threshold
If the top similarity score is below `retrieval.min_score`, the system refuses to answer from documents rather than guessing.

### Guardrails
Two-layer safety: (1) Deterministic rules (regex, blocklists), (2) Optional LLM auditor. If the LLM is unavailable, layer 1 alone decides (graceful degradation).

---

## 🔐 Security & Privacy

- **PII never logged**: Raw user messages are masked before storage
- **PII never sent to LLM**: Masking happens before LLM call
- **Workspace isolation**: SQL `WHERE workspace_id =` enforced in all queries
- **Citation verification**: Prevents hallucinated sources
- **Confidence threshold**: "I don't know" better than wrong answer
- **Secrets**: `.env` is git-ignored, use environment variables

---

## 🚀 Adding Your Own Workspace

1. **Create directory structure**:
```bash
mkdir -p workspaces/my-company/docs
```

2. **Create `workspace.yaml`**:
```yaml
slug: my-company
name: My Company Knowledge Base
description: Internal company policies and procedures
assistant_persona: You are a helpful assistant...
retrieval:
  top_k: 5
  min_score: 0.35
llm:
  model: gemini-1.5-flash
  temperature: 0.1
  max_tokens: 700
history_turns: 4
handoff_message: "Please contact HR for further assistance."
```

3. **Create `guardrails.yaml`** (copy from finance-demo and customize)

4. **Create `tools.yaml`** (empty for now):
```yaml
tools: []
```

5. **Add your PDFs** to `workspaces/my-company/docs/`

6. **Load and ingest**:
```bash
curl -X POST http://localhost:8000/api/workspaces/reload
python scripts/ingest.py --workspace my-company
```

7. **Test**:
```bash
curl -X POST http://localhost:8000/api/workspaces/my-company/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Your question here", "history": []}'
```

**That's it!** No code changes needed. The engine is 100% domain-agnostic.

---

## 🤝 Contributing

This is an educational/demonstration project. Contributions welcome!

### Development Setup

```bash
# Install dependencies
cd backend
pip install -r ../requirements.txt

# Run tests
pytest -v

# Lint & format
ruff check .
ruff format .
```

### Testing

```bash
# Run all tests (except live LLM tests)
pytest -v -m "not live"

# Run with live LLM tests (requires API key)
pytest -v
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LangChain/LangGraph** - Agent framework inspiration
- **pgvector** - Excellent PostgreSQL extension for vector search
- **sentence-transformers** - High-quality, local embeddings
- **Google Gemini** - Free, high-quality LLM API

---

## 📞 Support & Questions

- **Issues**: [GitHub Issues](https://github.com/Abhi0p2005/Grounded_AI/issues)
- **Testing Guide**: See [TESTING.md](TESTING.md)
- **Architecture Decisions**: See [docs/DECISIONS.md](docs/DECISIONS.md)

---

## 🗺️ Roadmap

### Short-term (Next Sprint)
- [ ] Tool calling with EMI calculator
- [ ] Full LangGraph agent with router
- [ ] Evaluation harness with metrics
- [ ] Second workspace (HR demo)

### Medium-term
- [ ] React frontend with citation UI
- [ ] Streaming responses
- [ ] Hybrid search (BM25 + vector)
- [ ] Reranking models

### Long-term
- [ ] Multi-language support
- [ ] Per-document access control
- [ ] Human-in-the-loop handoff
- [ ] Fine-grained analytics dashboard

---

## 📈 Performance

**Current benchmarks (MVP, single document query)**:
- **Ingestion**: ~10-30 seconds per PDF (depends on size)
- **Chat latency**: 1.5-3 seconds (LLM API dependent)
- **Vector search**: <100ms for top-5 similarity
- **Embedding model load**: ~2-3 seconds (first use only)

**Scalability notes**:
- Currently optimized for <1000 documents per workspace
- pgvector HNSW index scales to millions of vectors
- Consider reranking for >50 retrieved chunks

---

**Built with ❤️ for safe, grounded, measurable AI assistants.**

*Last updated: October 24, 2026*
