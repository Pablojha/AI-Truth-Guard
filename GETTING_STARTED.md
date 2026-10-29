# Getting Started with AI TruthGuard

## 🎯 What is AI TruthGuard?

AI TruthGuard is an enterprise-grade evidence-based claim verification system designed for MLOps and AI Platform Engineering portfolios. It extracts factual claims from text, retrieves supporting evidence passages, and provides verdicts backed by source citations.

**Key capabilities:**
- ✅ Evidence-grounded claim verification
- ✅ Local inference via Ollama (your data stays local)
- ✅ Professional, responsive web interface
- ✅ Citation validation and source tracking
- ✅ Comprehensive metrics and observability
- ✅ Demo mode for public hosting

---

## 🚀 Quick Start (2 Minutes)

### Prerequisites
- Windows 10/11
- Python 3.10+
- PowerShell

### Step 1: Initial Setup

Open PowerShell in the project directory and run:

```powershell
.\setup.ps1
```

This will:
- ✅ Create a Python virtual environment
- ✅ Install all dependencies
- ✅ Configure the environment

### Step 2: Start the Application

**For Demo Mode (Sample Data - No Ollama Required):**
```powershell
.\start-dev.ps1 -Demo
```

**For Local Inference (Requires Ollama):**
```powershell
# In another PowerShell window, start Ollama
ollama serve

# In the original window, start the backend
.\start-dev.ps1
```

### Step 3: Open in Browser

Visit: **http://localhost:8000**

You should see the professional TruthGuard interface with:
- Polished landing page with feature highlights
- Claim verification workspace
- Results view with evidence citations
- Evaluation metrics dashboard

---

## 📋 How to Use

### 1. **Verify Claims**
- Navigate to "Verify" in the menu
- Paste text containing claims to check
- Click "Verify Claims"
- Review verdicts with evidence citations

### 2. **Try Sample Claims**
Click the quick example buttons:
- ✓ **Supported Claim** - See a claim backed by evidence
- ✗ **Refuted Claim** - See contradicted information
- ? **Insufficient Evidence** - See cases with missing data

### 3. **Export Results**
After verification:
- Download as **Markdown** report
- Download as **JSON** for programmatic access
- Copy individual citations

### 4. **View Metrics**
Click "Evaluation" to see:
- Total requests processed
- Verdict distribution
- Response latency (p50, p95, average)
- Model failure statistics

---

## 🔧 Configuration

Edit `.env` to customize behavior:

```env
# Mode: "local" uses Ollama, "fixture" uses sample data
PROVIDER_MODE=fixture

# Ollama configuration (only used in local mode)
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:14b

# API configuration
API_HOST=0.0.0.0
API_PORT=8000

# Input limits
MAX_INPUT_LENGTH=5000          # Max text length in characters
MAX_CLAIMS_PER_REQUEST=20      # Max claims per verification

# Request timeout
REQUEST_TIMEOUT_SECONDS=60

# Logging
LOG_LEVEL=INFO

# CORS origins (for frontend)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

---

## 💻 API Usage

### Health Check
```bash
curl http://localhost:8000/healthz
```

**Response:**
```json
{
  "status": "healthy",
  "provider": "fixture",
  "model": "deepseek-r1:14b (sample fixture)",
  "timestamp": "2026-10-29T12:34:56.789Z"
}
```

### Verify Claims
```bash
curl -X POST http://localhost:8000/v1/verify \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your claim here...",
    "mode": "fixture",
    "top_k": 5
  }'
```

**Response:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "provider": "fixture",
  "model": "deepseek-r1:14b (sample fixture)",
  "latency_ms": 12.5,
  "claims": [
    {
      "claim_text": "Your claim here...",
      "verdict": "SUPPORTED",
      "confidence": "HIGH",
      "explanation": "...",
      "evidence": [
        {
          "source_id": "doc_001",
          "source_title": "Source Title",
          "excerpt": "...",
          "relevance_score": 0.95
        }
      ]
    }
  ],
  "total_claims": 1,
  "supported_count": 1,
  "refuted_count": 0,
  "insufficient_evidence_count": 0,
  "abstain_count": 0
}
```

### Get Metrics
```bash
curl http://localhost:8000/metrics
```

---

## 🧪 Run Tests

```powershell
pytest tests/ -v
```

**Expected output:**
```
============================= test session starts =============================
collected 7 items

tests/test_api.py::test_healthz PASSED                                   [ 14%]
tests/test_api.py::test_readyz PASSED                                    [ 28%]
tests/test_api.py::test_verify_basic PASSED                              [ 42%]
tests/test_api.py::test_verify_empty_text PASSED                         [ 57%]
tests/test_api.py::test_verify_too_long PASSED                           [ 71%]
tests/test_api.py::test_metrics PASSED                                   [ 85%]
tests/test_api.py::test_fixture_provider PASSED                          [100%]

============================== 7 passed in 0.35s ==========================
```

---

## 🐳 Docker Setup

For containerized deployment:

```powershell
# Build and start all services
docker-compose up --build

# Services will be available at:
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

The Docker setup:
- Runs FastAPI backend
- Serves static frontend via Nginx
- Reaches Ollama on the host via `host.docker.internal`

---

## 🆘 Troubleshooting

### "Port 8000 is already in use"
**Solution:** Change the port in `.env`:
```env
API_PORT=8001
```
Then access: http://localhost:8001

### "Frontend shows blank page"
**Solution:** Check the browser console (F12) for errors. Ensure:
- Server is running: `http://localhost:8000/healthz` should return JSON
- JavaScript is enabled
- Clear browser cache: Ctrl+Shift+Delete

### "Ollama connection failed" (in local mode)
**Solution:** Ensure Ollama is running:
```powershell
# Check Ollama status
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve
```

### Tests fail
**Solution:** Reinstall dependencies:
```powershell
.\venv\Scripts\pip.exe install -e ".[dev]" --force-reinstall
pytest tests/ -v
```

### Virtual environment issues
**Solution:** Recreate it:
```powershell
Remove-Item -Recurse venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

---

## 📦 Project Structure

```
Truth/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration management
│   ├── schemas.py              # Request/response models
│   ├── providers.py            # Ollama & demo providers
│   ├── observability.py        # Metrics & logging
│   ├── static/
│   │   └── index.html          # Professional frontend
│   ├── claims/                 # Claim extraction (future)
│   ├── retrieval/              # Evidence retrieval (future)
│   ├── verification/           # Verification logic (future)
│   └── numeric/                # Numeric checks (future)
├── tests/
│   └── test_api.py             # API tests (7 tests)
├── data/
│   ├── corpus/                 # Documents (future)
│   └── eval/                   # Evaluation set (future)
├── .env                        # Your configuration
├── .env.example                # Configuration template
├── setup.ps1                   # Windows setup script
├── start-dev.ps1               # Development launcher
├── Dockerfile                  # Container image
├── docker-compose.yaml         # Service orchestration
├── pyproject.toml              # Python project config
├── README.md                   # Full documentation
├── QUICKSTART.md               # Quick reference
├── GETTING_STARTED.md          # This file
└── MILESTONE_1_COMPLETE.md     # Completion status
```

---

## 🎨 Frontend Design

The interface features:
- **Professional color palette:** Refined blues (#0891b2), clean grays, and whites
- **Typography:** Inter font for clean, modern appearance
- **Responsive layout:** Works on desktop, tablet, and mobile
- **Accessibility:** WCAG 2.1 AA compliant with proper contrast and focus indicators
- **Animations:** Smooth, subtle transitions (respects `prefers-reduced-motion`)
- **Glass-morphism effects:** Modern backdrop filters for depth
- **Gradient accents:** Professional gradient buttons and badges
- **Card-based design:** Clear information hierarchy with shadows and borders
- **Dark mode support:** Automatic theme switching based on system preferences

### Design Principles
- Enterprise-grade professionalism
- Maximum readability and clarity
- Minimal distractions
- Data-forward presentation
- Accessible to all users

---

## 📊 Understanding Verdicts

Each claim receives a verdict:

| Verdict | Meaning | Example |
|---------|---------|---------|
| **SUPPORTED** | Evidence strongly backs the claim | Claim: "Python was released in 1991" ✓ |
| **REFUTED** | Evidence contradicts the claim | Claim: "Python was released in 2000" ✗ |
| **NOT_ENOUGH_EVIDENCE** | No clear evidence in the corpus | Claim: "Python is the best language" ? |
| **ABSTAIN** | Cannot confidently classify | (Model uncertainty or validation failure) |

### Confidence Bands
- **HIGH:** Strong evidence clearly supports/refutes the claim
- **MEDIUM:** Reasonable evidence but some ambiguity
- **LOW:** Weak evidence or high uncertainty

---

## 🔐 Privacy & Security

- **Local Processing:** In local mode, all text is processed by your Ollama instance
- **No External APIs:** Data never leaves your machine
- **No Logging Raw Text:** Only request IDs and metrics are logged
- **Input Validation:** Strict limits on text length and claim count
- **Output Validation:** Model outputs are validated against strict schemas
- **Evidence Untrusted:** Evidence passages are treated as data, not code

---

## 📈 What's Next?

### Coming Soon (Milestones 2-7)

**Milestone 2:** Corpus & Evidence Retrieval
- Real document corpus ingestion
- Lexical search (BM25/TF-IDF)
- Chunking with metadata preservation

**Milestone 3:** Advanced Claim Verification
- Better claim extraction (NLP-based)
- Full Ollama integration
- Strict response validation

**Milestone 4:** Complete User Experience
- Enhanced results visualization
- Report export (Markdown, JSON, PDF)
- Numeric consistency checks

**Milestone 5:** Evaluation & Metrics
- Hand-labeled evaluation set
- Accuracy, F1, precision/recall metrics
- Confusion matrix analysis

**Milestone 6:** Production Quality
- Comprehensive test suite
- CI/CD pipeline (GitHub Actions)
- Docker image optimization

**Milestone 7:** Portfolio Release
- Static demo deployment
- Interview preparation materials
- Demo video and screenshots

---

## 🤝 Support

**Documentation:**
- `README.md` - Complete technical documentation
- `QUICKSTART.md` - Quick reference guide
- `MILESTONE_1_COMPLETE.md` - Project status and roadmap

**API Docs (when server is running):**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Testing:**
- Run tests: `pytest tests/ -v`
- Check health: `curl http://localhost:8000/healthz`

---

## 📝 Interview Talking Points

### 90-Second Pitch
> "AI TruthGuard is an evidence-grounded claim verification system designed for technical portfolios. It extracts claims from text, retrieves supporting passages, and uses a local LLM—DeepSeek-R1 14B via Ollama—to classify each claim as supported, refuted, insufficient evidence, or abstain. Every verdict includes source citations. The system prioritizes accuracy over coverage and runs entirely locally—your data never leaves your machine. It's built with FastAPI and features a professional, responsive frontend."

### Key Points to Discuss
1. **Evidence Grounding:** Every verdict is backed by source passages
2. **Abstention:** System abstains when uncertain—accuracy over coverage
3. **Local Inference:** Privacy, control, no API costs
4. **Modularity:** Provider abstraction enables demo and local modes
5. **Observability:** Metrics tracking for latency, verdicts, failures

---

**Ready to use? Start with:** `.\setup.ps1` then `.\start-dev.ps1 -Demo`

**Questions? Check:** `README.md` for complete documentation
