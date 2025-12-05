"""
FastAPI Backend Application
Handles image predictions and model inference
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import uvicorn
from .predictor import predict_image
from .model_loader import load_model, get_model
from .database import save_prediction, get_latest_predictions
import io
from PIL import Image
import os
from datetime import datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    try:
        load_model()
        print("Model loaded successfully")
    except Exception as e:
        print(f"❌ Error loading model: {str(e)}")
        print("WARNING: Make sure your model file is in the models/ folder")
    yield
    # Shutdown (if needed)
    pass

app = FastAPI(
    title="Cotton Weed Detection API",
    description="API for detecting cotton weeds in images",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware to allow requests from Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.streamlit.app",  # Allow all Streamlit Cloud apps
        "http://localhost:8501",     # For local development
        "http://127.0.0.1:8501",     # For local development
        "*",  # Allow all (for VM access via IP)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response model
class PredictionResponse(BaseModel):
    boxes: List[List[float]]
    classes: List[str]
    confidences: List[float]
    num_detections: int

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Cotton Weed Detection API",
        "status": "running",
        "endpoints": {
            "predict": "/predict",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    model = get_model()
    return {
        "status": "healthy",
        "model_loaded": model is not None
    }

@app.get("/predictions/latest")
async def get_latest():
    """Get latest predictions for real-time sync"""
    predictions = get_latest_predictions(limit=10)
    return {"predictions": predictions}

@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)):
    """
    Predict weeds in uploaded image
    
    Args:
        file: Image file (jpg, png, etc.)
    
    Returns:
        JSON with bounding boxes, classes, and confidences
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Get predictions
        predictions = predict_image(image)
        
        if predictions is None:
            raise HTTPException(status_code=500, detail="Prediction failed")
        
        # Save prediction to database for real-time sync
        # Save image temporarily (optional - you can store in cloud storage instead)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = f"uploads/{timestamp}_{file.filename}"
        os.makedirs("uploads", exist_ok=True)
        image.save(image_path)
        
        save_prediction(image_path, predictions, device_type="api")
        
        return PredictionResponse(
            boxes=predictions["boxes"],
            classes=predictions["classes"],
            confidences=predictions["confidences"],
            num_detections=len(predictions["boxes"])
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

