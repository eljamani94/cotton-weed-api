# Cotton Weed Detection API

FastAPI backend for cotton weed detection using YOLOv8.

## Quick Start

### Local Development

\\\ash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
\\\

### Docker

\\\ash
docker build -t cotton-weed-api .
docker run -p 8000:8000 cotton-weed-api
\\\

## API Endpoints

- \GET /health\ - Health check
- \POST /predict\ - Upload image and get predictions
- \GET /docs\ - Interactive API documentation

## Deployment

This API is deployed on Render.com
