FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Copy requirements and install
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy logic and models
COPY --chown=user . .

# Expose generic port (HF Spaces uses 7860)
EXPOSE 7860

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
