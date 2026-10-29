# AI TruthGuard - Quick Start Guide

## 🚀 Get Running in 2 Minutes

### Step 1: Setup (First time only)

Open PowerShell in the project folder and run:

```powershell
.\setup.ps1
```

This will:
- ✓ Create virtual environment
- ✓ Install dependencies
- ✓ Create `.env` configuration

### Step 2: Start the Server

Choose demo or local mode:

**Demo Mode (Sample Data - No Ollama Needed):**
```powershell
.\start-dev.ps1 -Demo
```

**Local Mode (Requires Ollama Running):**
```powershell
# In another terminal, ensure Ollama is running
ollama serve

# Then start the server
.\start-dev.ps1
```

### Step 3: Open in Browser

```
http://localhost:8000
```

That's it! 🎉

---

## 📋 What You Can Do

1. **Verify Claims**
   - Paste text containing claims
   - Click "Verify Claims"
   - See verdicts with evidence citations

2. **Try Examples**
   - Click "✓ Supported Claim" to load a sample
   - Click "✗ Refuted Claim" to see a contradicted claim
   - Click "? Insufficient Evidence" to see cases with no clear answer

3. **View Metrics**
   - Click "Evaluation" in the menu
   - See request counts, verdict distribution, latency stats

4. **Export Results**
   - After verification, download as Markdown or JSON

---

## 🔧 Advanced

### Run Tests
```powershell
pytest tests/ -v
```

### Use Docker
```powershell
docker-compose up --build
```

### Manual Backend Start (without script)
```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Run API
python -m uvicorn app.main:app --reload
```

### Switch Provider Mode
Edit `.env`:
```
PROVIDER_MODE=fixture    # for demo
PROVIDER_MODE=local      # for Ollama
```

---

## 💬 API Examples

### Health Check
```powershell
curl http://localhost:8000/healthz
```

### Verify a Claim
```powershell
$body = @{
    text = "DeepSeek-R1 is a 14B model."
    mode = "fixture"
    top_k = 5
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:8000/v1/verify `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

### Get Metrics
```powershell
curl http://localhost:8000/metrics
```

---

## 🆘 Troubleshooting

### "Virtual environment not found"
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### "Ollama not reachable" (in local mode)
Ollama isn't running. Either:
- Use demo mode: `.\start-dev.ps1 -Demo`
- Or start Ollama: `ollama serve`

### "Port 8000 already in use"
Edit `start-dev.ps1` or `.env` to use a different port (e.g., 8001)

### Tests fail
```powershell
# Reinstall dependencies
pip install -e ".[dev]" --force-reinstall
pytest tests/ -v
```

---

## 📁 Project Layout

```
Truth/
├── app/              ← Backend code
├── tests/            ← Tests (run with pytest)
├── data/             ← Documents and evaluation (future)
├── start-dev.ps1     ← Quick start script
├── setup.ps1         ← Setup script
├── .env              ← Your configuration
├── README.md         ← Full documentation
└── MILESTONE_1_COMPLETE.md  ← Status and progress
```

---

## 🎯 What's Next?

- **Ready to verify claims?** Open http://localhost:8000
- **Want to use your own text?** Paste it in the "Verification Workspace"
- **Want to integrate locally?** Check the API endpoints in README.md
- **Ready for Milestone 2?** See MILESTONE_1_COMPLETE.md for next steps

---

## 📚 More Info

- Full docs: `README.md`
- Milestone status: `MILESTONE_1_COMPLETE.md`
- API reference: Start server, visit http://localhost:8000/docs
