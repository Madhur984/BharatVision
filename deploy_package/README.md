---
title: BharatVision ML API
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# BharatVision ML API

Cloud-hosted ML API for Legal Metrology Compliance using -2-9b-it.

This API provides AI-powered assistance for Legal Metrology compliance questions for the BharatVision application.

## Endpoints

- `GET /health` - Health check
- `POST /api/ai/ask` - Ask AI a question about Legal Metrology
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/search/products` - Search products
- `POST /api/upload/process` - Process uploaded images

## Usage

```bash
curl -X POST https://huggingface.co/spaces/YOUR_USERNAME/bharatvision-ml-api/api/ai/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is MRP?"}'
```
