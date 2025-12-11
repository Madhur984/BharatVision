FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libgl1 \
    pkg-config \
    ca-certificates \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first for better layer caching
COPY web/requirements.txt /app/web-requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /app/web-requirements.txt

# Copy app code
COPY . /app

EXPOSE 8501

CMD ["streamlit", "run", "web/streamlit_app.py", "--server.port=8501", "--server.headless=true"]
