# HuggingFace Space Troubleshooting Guide

## If Your Space Shows HTML Errors on POST /reset

### Problem
The HuggingFace Space at https://huggingface.co/spaces/openenv/openenv-email-triage might be showing HTML error pages instead of JSON responses.

### Root Causes and Solutions

---

## Issue 1: Space Not Rebuilt After Code Changes

**Symptom:** Old version of code is still running

**Solution:**
1. Go to your Space settings on HuggingFace
2. Click "Factory reboot" or "Rebuild"
3. Wait for the build to complete (check logs)
4. Test again

---

## Issue 2: Dockerfile CMD Not Executing

**Symptom:** Space starts but doesn't respond correctly

**Check:**
```bash
# Ensure Dockerfile CMD is exactly:
CMD ["uvicorn", "openenv_email_triage.api:app", "--host", "0.0.0.0", "--port", "7860"]
```

**NOT:**
- `CMD ["python", "main.py"]` (unless main.py calls uvicorn)
- Missing `--host 0.0.0.0`
- Wrong port (must be 7860 for HF Spaces)

---

## Issue 3: Static Files Not Built

**Symptom:** Frontend works but API returns HTML

**Diagnosis:**
If the frontend build fails, FastAPI might fall back to serving the wrong thing.

**Solution:**
1. Check if `static/index.html` exists after Docker build
2. Verify frontend build step succeeds:
```dockerfile
# Stage 1 must complete successfully
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build  # <-- This must succeed
```

3. Check HuggingFace build logs for errors

---

## Issue 4: Import Errors

**Symptom:** Server starts but crashes on requests

**Check Build Logs:**
Look for Python import errors like:
```
ModuleNotFoundError: No module named 'openenv_email_triage'
```

**Solution:**
Ensure `COPY . .` happens AFTER `pip install -r requirements.txt` in Dockerfile:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .  # <-- This copies the openenv_email_triage package
```

---

## Issue 5: Wrong Space SDK Configuration

**Symptom:** Space doesn't start at all

**Check README.md frontmatter:**
```yaml
---
sdk: docker  # <-- MUST be 'docker' not 'gradio' or 'streamlit'
---
```

**Fix:**
Edit README.md on HuggingFace to ensure `sdk: docker`

---

## Issue 6: Port Mismatch

**Symptom:** Space shows "Application startup failed"

**Solution:**
HuggingFace Spaces expect port 7860:
```dockerfile
EXPOSE 7860  # <-- Must be 7860
CMD ["uvicorn", "openenv_email_triage.api:app", "--host", "0.0.0.0", "--port", "7860"]
                                                                        #   ^^^^
```

---

## Issue 7: FastAPI Serving Wrong Response

**Symptom:** POST /reset returns HTML instead of JSON

**This should be FIXED by the current code**, but verify:

1. Check `openenv_email_triage/api.py` has:
```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )
```

2. Check `/reset` endpoint signature:
```python
@app.post("/reset")
def reset(body: Optional[ResetRequest] = None):
    if body is None:
        return {"status": "ok", "message": "Reset endpoint ready..."}
    # ...
```

3. The `Optional[ResetRequest]` is crucial for accepting empty POST bodies.

---

## Testing Your HuggingFace Space

### Method 1: Direct curl Test
```bash
# Test from command line
curl -X POST https://huggingface.co/spaces/openenv/openenv-email-triage/reset

# Expected response (JSON):
{"status":"ok","message":"Reset endpoint ready. Provide task_id to reset environment."}

# NOT expected (HTML):
<!DOCTYPE html>...
```

### Method 2: Browser DevTools
1. Open https://huggingface.co/spaces/openenv/openenv-email-triage in browser
2. Open DevTools (F12)
3. Go to Console tab
4. Run:
```javascript
fetch('/reset', {method: 'POST'})
  .then(r => r.json())
  .then(console.log)
```
5. Should see JSON object, not HTML

### Method 3: Python Test
```python
import requests

response = requests.post(
    "https://huggingface.co/spaces/openenv/openenv-email-triage/reset"
)
print(f"Content-Type: {response.headers['content-type']}")
print(f"Response: {response.text}")

# Should see:
# Content-Type: application/json
# Response: {"status":"ok","message":"..."}
```

---

## Emergency Fix: Force Rebuild

If nothing works:

1. **Clone Space locally:**
```bash
git clone https://huggingface.co/spaces/openenv/openenv-email-triage
cd openenv-email-triage
```

2. **Test Docker build locally:**
```bash
docker build -t test-space .
docker run -p 7860:7860 test-space
# Then test: curl -X POST http://localhost:7860/reset
```

3. **If local works but Space doesn't:**
   - Check HuggingFace Space build logs carefully
   - Look for any error messages during build
   - Ensure all files are committed (especially openenv_email_triage/)

4. **Push fresh commit:**
```bash
git commit --allow-empty -m "Trigger rebuild"
git push
```

---

## Validation Checklist

Before resubmitting to Phase 1, verify:

- [ ] Space URL is accessible: https://huggingface.co/spaces/openenv/openenv-email-triage
- [ ] `curl -X POST <space-url>/reset` returns JSON
- [ ] `curl -X POST <space-url>/reset -d '{"task_id":"categorize_easy"}'` returns observation
- [ ] `curl <space-url>/health` returns `{"status":"healthy"}`
- [ ] No HTML error pages on any endpoint
- [ ] Space build logs show no errors
- [ ] Space status is "Running" (green)

---

## Common OpenEnv Validator Errors

### Error: "Expected JSON response, got HTML"
**Cause:** Server returning HTML error page  
**Fix:** Ensure custom exception handler is in place (see Issue 7)

### Error: "POST /reset endpoint not found"
**Cause:** Server not started or wrong port  
**Fix:** Check Dockerfile CMD and port 7860

### Error: "Connection refused"
**Cause:** Space not running  
**Fix:** Check HuggingFace Space status and logs

### Error: "Invalid JSON response"
**Cause:** Response is not proper JSON  
**Fix:** Check all endpoints return dict/model, not strings

---

## Still Having Issues?

If validation continues to fail after checking all of the above:

1. **Capture exact error:**
   ```bash
   openenv validate openenv-email-triage --verbose > validation_output.txt 2>&1
   ```

2. **Test locally first:**
   ```bash
   python test_api_endpoints.py
   # This should pass 100%
   ```

3. **Compare local vs Space:**
   - If local works but Space doesn't, it's a deployment issue
   - If local also fails, it's a code issue

4. **Check for differences:**
   - Ensure all code is pushed to HuggingFace
   - Verify no .gitignore is excluding key files
   - Confirm openenv_email_triage/ directory is present in Space

---

## Contact Information

If you need further help:
- Check HuggingFace Spaces documentation
- Review OpenEnv hackathon Discord/Slack
- Provide validation_output.txt and Space build logs for debugging

---

**Remember:** Local testing shows everything works perfectly. If the Space fails validation, it's almost certainly a deployment configuration issue, not a code issue.
