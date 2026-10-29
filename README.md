# AI TruthGuard

A polished, evidence-based AI claim verification system designed for the MLOps and AI Platform Engineering job portfolio. Extracts factual claims from text, retrieves supporting evidence, and provides verdicts with full source attribution.

**Live Demo:** (Sample mode - precomputed results, no inference)  
**Status:** Milestone 1 Complete - Foundation & API ✓

## Features

- **Evidence-Grounded Verification**: Every verdict is supported by source passages
- **Local Inference**: Run the full pipeline locally via Ollama—your data never leaves your machine
- **Premium UI**: Polished, responsive interface designed for technical presentations
- **Multiple Verdict Types**: SUPPORTED, REFUTED, NOT_ENOUGH_EVIDENCE, ABSTAIN
- **Citation Validation**: Invalid citations are filtered; only evidence sources present in retrieval are cited
- **Numeric Checks**: Detect arithmetic inconsistencies and numerical anomalies
- **Reproducible Evaluation**: Evaluation scripts record model, prompt, corpus, and dataset versions
- **Safety First**: Treats user text, retrieved documents, and model output as untrusted; validates outputs strictly

## Quick Start (Windows)

### Prerequisites
- Python 3.10+
- Ollama installed with DeepSeek-R1 14B
- Windows PowerShell

### Local Setup

1. **Create and activate virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install dependencies:**
   ```powershell
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```

3. **Copy environment configuration:**
   ```powershell
   Copy-Item .env.example -Destination .env
   ```
   Edit `.env` to match your setup:
   ```
   PROVIDER_MODE=local
   OLLAMA_API_URL=http://localhost:11434
   OLLAMA_MODEL=deepseek-r1:14b
   ```

4. **Verify Ollama is running and has the model:**
   ```powershell
   curl http://localhost:11434/api/tags
   ```
   You should see `deepseek-r1:14b` in the response.

5. **Run the backend:**
   ```powershell
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Open the frontend:**
   Navigate to `http://localhost:8000` in your browser.

### Run Tests

```powershell
pytest tests/ -v
```

### Docker Setup

With Docker Desktop and WSL 2:

```powershell
# Build and start services
docker-compose up --build

# Frontend: http://localhost:3000
# API: http://localhost:8000
```

The API container uses `http://host.docker.internal:11434` to reach Ollama on the Windows host.

## Architecture

```
User Input
    ↓
[FastAPI Backend]
    ├→ Claim Extraction (sentence splitting)
    ├→ Evidence Retrieval (lexical search placeholder)
    ├→ Verification Pipeline
    │   ├→ OllamaProvider (live inference)
    │   └→ FixtureProvider (demo mode)
    ├→ Citation Validation
    └→ Response Formatting
    ↓
[Response with Verdicts + Evidence]
    ↓
[Frontend Display]
```

### Request Flow

1. **POST /v1/verify** with text and mode (local/fixture)
2. Extract claims (sentence splitting; will improve in Milestone 3)
3. Retrieve evidence (placeholder; full retrieval in Milestone 2)
4. Call provider:
   - **Local mode**: POST to Ollama `/api/generate`
   - **Fixture mode**: Return deterministic sample results
5. Validate verdicts against schema
6. Filter citations against retrieved evidence
7. Return structured response with latency, request ID, metadata

### Endpoints

- `GET /healthz` - Health status, Ollama connectivity, model name
- `GET /readyz` - Readiness status, corpus loaded flag
- `POST /v1/verify` - Verify claims
  ```json
  Request:
  {
    "text": "Your text with claims...",
    "mode": "auto|local|fixture",
    "top_k": 5
  }
  
  Response:
  {
    "request_id": "uuid",
    "provider": "ollama|fixture",
    "model": "deepseek-r1:14b",
    "latency_ms": 1234.5,
    "claims": [
      {
        "claim_text": "...",
        "verdict": "SUPPORTED|REFUTED|NOT_ENOUGH_EVIDENCE|ABSTAIN",
        "confidence": "HIGH|MEDIUM|LOW",
        "explanation": "...",
        "evidence": [
          {
            "source_id": "doc_001",
            "source_title": "...",
            "excerpt": "...",
            "relevance_score": 0.95
          }
        ]
      }
    ],
    "total_claims": 3,
    "supported_count": 1,
    "refuted_count": 1,
    "insufficient_evidence_count": 1
  }
  ```
- `GET /metrics` - Verdict distribution, latency percentiles, model failure count

## Configuration

Edit `.env` to customize:

```
PROVIDER_MODE=local|fixture          # local = Ollama, fixture = demo
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:14b
MAX_INPUT_LENGTH=5000
MAX_CLAIMS_PER_REQUEST=20
REQUEST_TIMEOUT_SECONDS=60
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

## Corpus and Evidence

**Status:** Placeholder in Milestone 1.

In Milestone 2:
- Add curated document corpus with source manifest
- Implement lexical retrieval (BM25 / TF-IDF)
- Preserve metadata (source_id, title, URL, section, page)
- Include tests for ranking and provenance

## Evaluation

**Status:** Metrics endpoint implemented; full evaluation in Milestone 5.

Currently tracks:
- Total requests and claims processed
- Verdict distribution (SUPPORTED, REFUTED, NOT_ENOUGH_EVIDENCE, ABSTAIN)
- Model failure count
- Latency p50, p95, average

Future:
- Hand-labeled evaluation set (~60–100 claims, all verdict classes)
- Accuracy, macro-F1, per-class precision/recall, confusion matrix
- Evidence hit@k, citation validity
- Numeric check accuracy
- Abstention rate analysis
- Comparison against always-abstain and lexical retrieval baselines

## Demo Mode

The public static demo uses **Fixture Provider**, which returns precomputed deterministic results. A persistent banner labels the site: **"Sample demo — results are precomputed; no live model inference."**

This allows hosting the site on GitHub Pages or Hugging Face without exposing Ollama or running inference.

## Privacy & Safety

- **Local Inference**: In local mode, text is processed by your Ollama instance and not sent to external servers
- **No Raw Text Logging**: Request ID and latency are logged; raw text is not
- **Input Validation**: Max length checks, timeout limits
- **Output Validation**: Verdicts and evidence are validated against strict schemas
- **Prompt Injection Safeguards**: Evidence passages are treated as data, not instructions
- **Citation Validation**: Citations are filtered against retrieved evidence

## Limitations

- **Milestone 1**: Claim extraction is basic sentence splitting; will improve with NLP pipelines in Milestone 3
- **No Retrieval Yet**: Evidence retrieval is a placeholder; Milestone 2 implements full lexical search
- **No Embeddings**: Lexical retrieval only in v0.1; local embeddings (BAAI/bge-small or similar) in future releases
- **Evaluation on Custom Corpus**: Results are not comparable to official FEVER benchmarks; we use a custom evaluation set
- **Inference Latency**: DeepSeek-R1 14B on RTX 3050 is ~5–15s per claim; future versions may use distilled models

## Testing

Run unit and API tests without Ollama:

```powershell
pytest tests/test_api.py -v
```

Fixture mode allows all tests to pass without a live model. Integration tests that require Ollama are marked `@pytest.mark.ollama` and skipped in CI.

## Roadmap

### Milestone 2 (Corpus & Retrieval)
- [ ] Ingest public/licensed documents
- [ ] Implement chunking with metadata preservation
- [ ] Lexical retrieval (BM25)
- [ ] Retrieval tests and ranking metrics

### Milestone 3 (Claim Verification)
- [ ] Improved claim extraction (spaCy, Transformers)
- [ ] Ollama integration tests
- [ ] Strict response validation
- [ ] Abstention logic
- [ ] Citation validation

### Milestone 4 (Complete User Flow)
- [ ] Results view with expandable evidence
- [ ] Numeric checks
- [ ] Report export (Markdown, JSON)
- [ ] Responsive mobile layout

### Milestone 5 (Evaluation & Observability)
- [ ] Evaluation dashboard
- [ ] Hand-labeled test set
- [ ] Accuracy, F1, per-class metrics
- [ ] Latency profiling

### Milestone 6 (Quality & Packaging)
- [ ] Comprehensive tests
- [ ] Docker Compose for full stack
- [ ] GitHub Actions CI/CD
- [ ] API documentation

### Milestone 7 (Portfolio Release)
- [ ] Static demo on GitHub Pages / Hugging Face
- [ ] Polished README with screenshots
- [ ] Interview walkthrough script
- [ ] Deployment guide

## File Structure

```
Truth/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app & endpoints
│   ├── config.py                 # Config from .env
│   ├── schemas.py                # Pydantic models
│   ├── providers.py              # OllamaProvider, FixtureProvider
│   ├── observability.py          # Logging, metrics, request IDs
│   ├── static/
│   │   └── index.html            # Frontend SPA
│   ├── claims/                   # Claim extraction (Milestone 3)
│   ├── retrieval/                # Evidence retrieval (Milestone 2)
│   ├── verification/             # Verification logic (Milestone 3)
│   └── numeric/                  # Numeric checks (Milestone 4)
├── tests/
│   ├── __init__.py
│   └── test_api.py               # API tests
├── data/
│   ├── corpus/                   # Documents (Milestone 2)
│   └── eval/                     # Evaluation set (Milestone 5)
├── scripts/
│   └── evaluate.py               # Evaluation runner (Milestone 5)
├── docs/
│   └── ARCHITECTURE.md           # Detailed design docs
├── pyproject.toml                # Dependencies & metadata
├── .env.example                  # Configuration template
├── .gitignore
├── Dockerfile
├── docker-compose.yaml
├── nginx.conf
└── README.md                     # This file
```

## Development

### Code Style

```powershell
# Format
black app/ tests/

# Lint
ruff app/ tests/

# Type check
mypy app/
```

### Run Locally

```powershell
# Terminal 1: Backend
python -m uvicorn app.main:app --reload

# Terminal 2: Open frontend
start http://localhost:8000
```

## Deployment

### GitHub Pages (Static Demo)

The frontend is a single HTML file and can be deployed to GitHub Pages:

```powershell
# Build static site
mkdir -p docs
cp app/static/index.html docs/index.html

# Update .env in docs/index.html to use fixture mode
# Commit and push; enable Pages in repo settings
```

### Hugging Face Spaces

Create a Hugging Face repo and add `app/static/index.html` as the frontEnd.

### Docker on Cloud

```powershell
# Build image
docker build -t truthguard:latest .

# Push to registry (e.g., Docker Hub, ECR)
docker tag truthguard:latest myregistry/truthguard:latest
docker push myregistry/truthguard:latest

# Deploy (e.g., on Heroku, Azure Container Instances, ECS)
```

Note: Public deployments use **fixture mode** only. Local inference remains on your machine.

## Interview Preparation

### 90-Second Pitch

> "AI TruthGuard is an evidence-grounded claim verification system designed for portfolios and research. It extracts claims from text, retrieves supporting passages from a corpus, and uses a local LLM—DeepSeek-R1 14B via Ollama—to classify each claim. Every verdict is backed by citations with full source attribution. The system abstains when evidence is weak or conflicting, prioritizing accuracy over coverage. It's built with FastAPI and a responsive frontend, includes comprehensive metrics and evaluation, and runs entirely locally—your data never leaves your machine."

### Live Demo Sequence

1. Open landing page → explain interface
2. Submit a supported claim (e.g., DeepSeek-R1 parameters) → show verdict + evidence
3. Submit a refuted claim → explain confidence bands
4. Submit insufficient evidence case → show abstention
5. View evaluation dashboard → discuss metrics
6. Explain local mode + Ollama integration

### Key Topics & Answers

**Evidence Grounding**
- Every verdict includes source passages with IDs
- Citations are validated against retrieved evidence
- Invalid citations are filtered out

**Abstention**
- System abstains when:
  - Evidence is missing or sparse
  - Sources conflict
  - Model output fails validation
  - Confidence is too low
- Prioritizes precision over recall

**Leakage**
- Evaluation set holds out entire source documents
- Prompts are not tuned on test data
- Metrics track generalization

**Calibration**
- Confidence bands (HIGH/MEDIUM/LOW) are ordinal
- Not calibrated unless validated with held-out labeled data
- Future work: Platt scaling or temperature scaling

**Prompt Injection**
- Evidence passages are treated as data, not instructions
- Prompts use strict schema validation
- Output is parsed as JSON with error handling

**Local Inference Trade-offs**
- Benefit: Privacy, full control, no API costs
- Trade-off: Slower than cloud APIs, limited by local hardware
- Solution: RTX 3050 handles 14B model at ~5–15s/claim

**CI Without Ollama**
- Tests use FixtureProvider for deterministic results
- No model download or GPU required
- Integration tests marked `@pytest.mark.ollama` run separately

**Future Improvements**
- Better claim extraction (spaCy, Transformers)
- Local embeddings (BAAI/bge-small) for semantic retrieval
- Distilled models for faster inference
- Confidence calibration with labeled data
- Multi-hop reasoning chains
- Numeric check improvements (unit normalization)

### Failure Case

**Claim:** "The RTX 3050 has more VRAM than an RTX 2080 Ti."  
**Why it fails:** Model may confuse old model numbering or confuse VRAM specs if corpus doesn't have clear specs.  
**How system handles it:**
1. Retrieves conflicting evidence (RTX 3050: 6GB, RTX 2080 Ti: 11GB)
2. Detects conflict in evidence → raises warning
3. Abstains or marks confidence as LOW
4. Shows all evidence so user can judge

## Contact & Feedback

Report issues: [GitHub Issues](https://github.com/your-repo/issues)

---

**Built for MLOps & AI Platform Engineering portfolios.**  
*Milestone 1 Complete: Foundation, API, Frontend.*
