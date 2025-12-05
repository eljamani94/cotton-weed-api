# FastAPI Backend Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==20.1.0

# Copy application code
COPY api/ ./api/
COPY models/ ./models/

# Create uploads directory and non-root user
RUN adduser --disabled-password --gecos "" appuser && \
    mkdir -p /app/uploads && \
    chown -R appuser:appuser /app
USER appuser

# Run with gunicorn for production
# Use 1 worker to reduce memory usage and startup time on free tier
# Increase timeout to 300s to allow model loading
CMD gunicorn -k uvicorn.workers.UvicornWorker -w 1 -t 300 --bind 0.0.0.0:${PORT:-10000} --keep-alive 5 --access-logfile - --error-logfile - --log-level info api.main:app

