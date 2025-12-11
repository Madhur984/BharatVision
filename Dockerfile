
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV and Surya
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage caching
COPY requirements_space.txt .
RUN pip install --no-cache-dir -r requirements_space.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/cache
ENV SURYA_CACHE=/app/cache

# Create cache directory with permissions
RUN mkdir -p /app/cache && chmod 777 /app/cache

# Run the API
CMD ["uvicorn", "simple_api:app", "--host", "0.0.0.0", "--port", "7860"]
