# Troubleshooting Guide - AI TruthGuard

## "The Link Isn't Opening" - Step-by-Step Fix

### 1. **Make Sure the Server is Running**

Open **TWO PowerShell windows:**

**Window 1: Start the Server**
```powershell
cd "C:\Users\Aman jha\Truth"
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Window 2: Open Browser**
```powershell
Start-Process "http://localhost:8000"
```

### 2. **If Browser Still Shows Blank/Error**

Try these URLs in order:

| URL | Use if... |
|-----|-----------|
| `http://localhost:8000` | Browser is on same machine |
| `http://127.0.0.1:8000` | localhost doesn't work |
| `http://0.0.0.0:8000` | Try this if above fails |

### 3. **Check the Server is Actually Running**

In **Window 1** (where server is running), you should see:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

If you see errors, scroll up and read them.

### 4. **Verify the Setup**

Run this in PowerShell:
```powershell
cd "C:\Users\Aman jha\Truth"

# Check virtual environment
.\venv\Scripts\python.exe --version
# Should show: Python 3.11.x

# Check dependencies
.\venv\Scripts\python.exe -m pip list | Select-String fastapi
# Should show: fastapi 0.162.0

# Check HTML file exists
Test-Path "app/static/index.html"
# Should show: True
```

### 5. **Check Firewall/Port Issues**

```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# If something is using it, either:
# - Kill the process: taskkill /PID [PID] /F
# - Use different port: Edit .env and change API_PORT to 8001
```

### 6. **Common Issues & Fixes**

| Problem | Solution |
|---------|----------|
| "ModuleNotFoundError: No module named 'app'" | Run from project root: `cd "C:\Users\Aman jha\Truth"` |
| "Port 8000 in use" | Change `API_PORT` in `.env` or kill existing process |
| "Blank white page" | Server is running but frontend has JavaScript error - open DevTools (F12) |
| "Cannot GET /" | Static files not found - check `app/static/index.html` exists |
| "Connection refused" | Server isn't running - check Window 1 |

---

## Quick Restart Procedure

If nothing works, try a clean restart:

### Step 1: Stop Everything
```powershell
# Kill all Python processes
taskkill /F /IM python.exe

# Wait
Start-Sleep -Seconds 2
```

### Step 2: Activate Virtual Environment
```powershell
cd "C:\Users\Aman jha\Truth"
.\venv\Scripts\Activate.ps1
```

### Step 3: Start Server
```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Open in Browser
Open a new PowerShell window and run:
```powershell
Start-Process "http://localhost:8000"
```

---

## Using the Convenience Scripts

### Method 1: Using `start-dev.ps1`

**Option A: Demo Mode (No Ollama)**
```powershell
.\start-dev.ps1 -Demo
```

**Option B: Local Mode (With Ollama)**
```powershell
# First make sure Ollama is running
ollama serve

# In another window:
.\start-dev.ps1
```

### Method 2: Manual Start (Simpler Debugging)
```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Start server with explicit options
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Verify It's Working

Once the server is running, open another PowerShell window and test:

```powershell
# Test health endpoint
curl.exe http://localhost:8000/healthz

# You should see JSON like:
# {"status":"healthy","provider":"fixture","model":"deepseek-r1:14b (sample fixture)"...}
```

If you get valid JSON back, the server is working fine and it's a browser/JavaScript issue.

---

## Debug: Open Browser DevTools

1. **Open the page:** http://localhost:8000
2. **Press F12** to open DevTools
3. **Go to Console tab**
4. **Look for red errors** - take a screenshot
5. **Check Network tab** - look for failed requests (red X)

Common errors:
- **"Cannot access API"** - Server not running
- **"CORS error"** - Check CORS_ORIGINS in .env
- **"Fetch failed"** - Network issue or wrong URL

---

## The Absolute Easiest Way

Copy-paste this entire command:

```powershell
cd "C:\Users\Aman jha\Truth" && .\venv\Scripts\Activate.ps1 && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Then in browser: `http://localhost:8000`

If this doesn't work, something is wrong with the Python installation.

---

## If Still Stuck

Try this diagnostic:

```powershell
cd "C:\Users\Aman jha\Truth"

# 1. Check Python works
python --version

# 2. Check pip can find packages
python -m pip show fastapi

# 3. Try importing manually
python -c "import app.main; print('App imports OK')"

# 4. Check static files exist
Get-ChildItem app/static/

# 5. Try running tests
pytest tests/test_api.py -v
```

Post the output of these commands if you're still having issues.

---

## Using Docker (Alternative)

If the manual setup is problematic, use Docker:

```powershell
# Build and start
docker-compose up --build

# Then open: http://localhost:3000 (for frontend)
#        or: http://localhost:8000 (for API)
```

---

## Windows Defender/Antivirus

Some antivirus software blocks local network services. If you see connection refused:

1. Add Python to Windows Defender exceptions
2. Or add port 8000 to allowed ports
3. Or temporarily disable the antivirus to test

---

## Still Not Working?

Please provide:
1. **What command you ran** (copy-paste the exact command)
2. **What error you see** (copy full error message)
3. **Output of:** `python --version`
4. **Output of:** `python -m pip show fastapi`

Then I can help debug specifically.

---

## The Expected Experience

When working correctly:

1. ✅ Run setup script: `.\setup.ps1` (one-time)
2. ✅ Start server: `.\start-dev.ps1` (or manual command)
3. ✅ Wait 3 seconds for startup message
4. ✅ Open browser: `http://localhost:8000`
5. ✅ See professional landing page with "AI TruthGuard" title
6. ✅ Click "Start Checking Claims"
7. ✅ Load sample claim → See results with badges and evidence
8. ✅ Export as JSON
9. ✅ View metrics dashboard

If any step fails, this guide should help you fix it.
