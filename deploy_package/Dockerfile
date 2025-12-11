# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements_api.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_api.txt

# Copy application file
COPY simple_api.py .

# Expose port (HuggingFace Spaces uses port 7860 by default)
EXPOSE 7860

# Set environment variable for port
ENV PORT=7860

# Run the application
CMD uvicorn simple_api:app --host 0.0.0.0 --port $PORT --workers 2
