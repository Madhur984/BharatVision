FROM python:3.11-slim

WORKDIR /app

# Install minimal system deps required by some CV/ocr packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (full heavy stack)
COPY ../requirements.full.txt ./requirements.full.txt

RUN python -m pip install --upgrade pip
## Install PyTorch CPU wheels first to improve wheel resolution on builders
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    "torch==2.1.2" "torchvision==0.16.2" --no-deps || true

# Then install the rest of the requirements
RUN pip install --no-cache-dir -r requirements.full.txt

# Copy backend code
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "backend.inference:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
