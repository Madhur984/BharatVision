# BharatVision Security & Testing Setup Guide

## 🔒 Security Improvements Implemented

### 1. CORS Configuration
**Before:**
```python
allow_origins=["*"]  # ❌ Accepts requests from ANY origin
```

**After:**
```python
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8501").split(",")
allow_origins=allowed_origins  # ✅ Only specific origins allowed
```

**Configuration:**
Set in `.env` file:
```bash
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8501,https://yourdomain.com
```

### 2. Rate Limiting
- **Default:** 60 requests per minute per IP
- **Configurable** via `API_RATE_LIMIT` environment variable
- **Headers:** Returns `X-RateLimit-*` headers with each response
- **Response:** 429 Too Many Requests when exceeded

### 3. Security Headers
All API responses now include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`
- `Content-Security-Policy: default-src 'self'`

### 4. Input Validation
- **Pydantic schemas** with validators
- **Prevents injection attacks** via special character filtering
- **Type checking** and range validation
- **Automatic API documentation** via OpenAPI

### 5. Environment Variables
- **`.env.example`** template provided
- **`.gitignore`** updated to exclude `.env` files
- **No credentials** in version control

---

## 🧪 Testing Setup

### Test Structure
```
tests/
├── conftest.py              # Pytest configuration & fixtures
├── unit/
│   ├── test_ocr_integration.py
│   └── test_compliance_validator.py
└── integration/
    └── test_api_endpoints.py
```

### Running Tests

#### Install Development Dependencies
```bash
pip install -r requirements-dev.txt
```

#### Run All Tests
```bash
pytest tests/ -v
```

#### Run Specific Test Suite
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_ocr_integration.py -v
```

#### Run with Coverage
```bash
pytest tests/ --cov=backend --cov-report=html
```

View coverage report: `open htmlcov/index.html`

---

## 🎨 Code Quality Tools

### Pre-commit Hooks

#### Installation
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

#### Manual Run
```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

### What Gets Checked
- ✅ **Black** - Code formatting
- ✅ **isort** - Import sorting
- ✅ **flake8** - Linting
- ✅ **mypy** - Type checking
- ✅ **bandit** - Security scanning
- ✅ **detect-secrets** - Credential detection

### Manual Code Quality Checks

#### Format Code
```bash
black backend/ --line-length=100
isort backend/ --profile=black
```

#### Lint Code
```bash
flake8 backend/ --max-line-length=100
```

#### Type Check
```bash
mypy backend/ --ignore-missing-imports
```

#### Security Scan
```bash
bandit -r backend/ -ll
```

---

## 🚀 Quick Start (Updated)

### 1. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Install Dependencies
```bash
# Production dependencies
pip install -r requirements.txt

# Development dependencies (for testing)
pip install -r requirements-dev.txt
```

### 3. Setup Pre-commit Hooks
```bash
pre-commit install
```

### 4. Run Tests
```bash
pytest tests/ -v
```

### 5. Start API Server
```bash
cd backend
python api_server.py
```

The API will be available at: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

---

## 📊 API Changes

### New Response Headers
All API responses now include:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1705764000
X-Process-Time: 0.123
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

### Enhanced Error Responses
```json
{
  "error": "ValidationError",
  "message": "Invalid input data",
  "details": {
    "field": "price",
    "issue": "must be positive"
  },
  "timestamp": "2026-01-20T15:00:00Z"
}
```

### Rate Limit Response (429)
```json
{
  "error": "Rate limit exceeded",
  "message": "Maximum 60 requests per minute allowed",
  "retry_after": 60
}
```

---

## 🔐 Security Best Practices

### ✅ DO
- Use `.env` for sensitive configuration
- Set specific CORS origins in production
- Monitor rate limit logs for abuse
- Keep dependencies updated
- Run security scans regularly

### ❌ DON'T
- Commit `.env` files to git
- Use `allow_origins=["*"]` in production
- Disable rate limiting without good reason
- Skip input validation
- Ignore security warnings from bandit

---

## 📝 Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:8501` | Comma-separated CORS origins |
| `API_RATE_LIMIT` | `60` | Requests per minute per IP |
| `SECRET_KEY` | - | Application secret key |
| `JWT_SECRET_KEY` | - | JWT signing key |
| `DATABASE_URL` | `sqlite:///./bharatvision.db` | Database connection string |
| `DEVICE` | `auto` | ML device (cuda/cpu/auto) |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## 🐛 Troubleshooting

### Rate Limiting Issues
**Problem:** Getting 429 errors during development

**Solution:**
```bash
# Increase rate limit in .env
API_RATE_LIMIT=1000
```

### CORS Errors
**Problem:** Browser shows CORS error

**Solution:**
```bash
# Add your frontend URL to .env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8501,http://yourdomain.com
```

### Test Failures
**Problem:** Tests fail with import errors

**Solution:**
```bash
# Ensure you're in project root
cd /path/to/BharatVision

# Install test dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v
```

---

## 📚 Additional Resources

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/usage/validators/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Pre-commit Hooks](https://pre-commit.com/)

---

## 🎯 Next Steps

1. **Review** the security changes
2. **Configure** your `.env` file
3. **Run** the test suite
4. **Enable** pre-commit hooks
5. **Deploy** with new security settings

---

*Last Updated: January 20, 2026*
