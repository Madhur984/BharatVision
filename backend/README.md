# Inference Backend

This directory contains a lightweight FastAPI inference service that runs the full
ML/CV OCR pipeline. The backend is intended to be deployed separately from the
Streamlit web UI so heavy packages (torch, ultralytics, etc.) do not need to be
installed in the web runtime.

Quick start (build and run with Docker):

```bash
# from repository root
docker build -f backend/Dockerfile -t lmpc-inference:latest .
docker run -p 8000:8000 lmpc-inference:latest
```

Health check:

```
curl http://localhost:8000/health
```

Inference endpoint:

POST `/infer` with multipart form `file` -> returns JSON result similar to the web UI.

Environment variable:
- `INFERENCE_BACKEND_URL` - configure the front-end to point to the remote backend (default: `http://localhost:8000/infer`).
