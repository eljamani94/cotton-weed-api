# FastAPI Backend Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PORT=8000 \
    WORKERS_PER_CORE=1 \
    MAX_WORKERS=4 \
    TIMEOUT=120 \
    KEEP_ALIVE=5

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

# Create a non-root user and switch to it
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Run with gunicorn for production
CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker -w $WORKERS_PER_CORE --max-workers $MAX_WORKERS -t $TIMEOUT --bind 0.0.0.0:${PORT} --keep-alive $KEEP_ALIVE api.main:app"]

