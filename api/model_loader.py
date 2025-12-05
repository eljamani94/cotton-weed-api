"""
Model Loading Module
Loads the trained model based on file format
"""
import os
import torch
import torch.nn as nn
from typing import Optional

# Global model variable
_model = None
_model_path = None
_model_type = None  # 'yolo', 'pytorch', 'tensorflow', 'onnx'

def get_model_path():
    """Get the path to the model file"""
    # Get the project root directory (parent of api/ folder)
    current_file = os.path.abspath(__file__)
    api_dir = os.path.dirname(current_file)
    project_root = os.path.dirname(api_dir)  # Go up one level from api/ to project root
    
    # Check common model locations (relative to project root)
    possible_paths = [
        os.path.join(project_root, "models", "yolov8n_best_model.pt"),  # YOLOv8 model
        os.path.join(project_root, "models", "model.pth"),
        os.path.join(project_root, "models", "model.pt"),
        os.path.join(project_root, "models", "best_model.pth"),
        os.path.join(project_root, "models", "weights.pth"),
        os.path.join(project_root, "models", "cotton_weed_model.pth"),
        # Also check relative to current working directory
        "models/yolov8n_best_model.pt",
        "models/model.pth",
        "models/model.pt",
        "models/best_model.pth",
        "../models/yolov8n_best_model.pt",
        "../models/model.pth",
        "../models/model.pt",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return os.path.abspath(path)  # Return absolute path
    
    # List available files in models directory
    models_dirs = [
        os.path.join(project_root, "models"),
        "models",
        "../models"
    ]
    
    for models_dir in models_dirs:
        if os.path.exists(models_dir):
            files = os.listdir(models_dir)
            model_files = [f for f in files if f.endswith(('.pth', '.pt', '.h5', '.onnx', '.pb'))]
            if model_files:
                return os.path.abspath(os.path.join(models_dir, model_files[0]))
    
    return None

def load_model(model_path: Optional[str] = None):
    """
    Load the trained model
    
    Args:
        model_path: Path to model file. If None, will search for model files.
    
    Returns:
        Loaded model
    """
    global _model, _model_path, _model_type
    
    if model_path is None:
        model_path = get_model_path()
    
    if model_path is None:
        raise FileNotFoundError(
            "Model file not found. Please place your trained model in the 'models/' folder.\n"
            "Supported formats: .pth, .pt, .h5, .onnx, .pb"
        )
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at: {model_path}")
    
    print(f"Loading model from: {model_path}")
    
    # Determine model format and load accordingly
    file_ext = os.path.splitext(model_path)[1].lower()
    filename = os.path.basename(model_path).lower()
    
    try:
        # Check if it's a YOLOv8 model (by filename or by trying to load with ultralytics)
        if 'yolo' in filename or 'yolov8' in filename:
            try:
                from ultralytics import YOLO
                _model = YOLO(model_path)
                _model_type = 'yolo'
                print("YOLOv8 model loaded successfully")
                _model_path = model_path
                return _model
            except ImportError:
                print("WARNING: ultralytics not installed. Trying standard PyTorch loading...")
            except Exception as e:
                print(f"WARNING: Failed to load as YOLO model: {e}. Trying standard PyTorch loading...")
        
        if file_ext in ['.pth', '.pt']:
            # PyTorch model
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            print(f"Using device: {device}")
            
            # Try loading as YOLO first (even if filename doesn't suggest it)
            try:
                from ultralytics import YOLO
                _model = YOLO(model_path)
                _model_type = 'yolo'
                print("YOLOv8 model loaded successfully")
                _model_path = model_path
                return _model
            except:
                pass
            
            # Try loading as full model first
            try:
                _model = torch.load(model_path, map_location=device)
                if isinstance(_model, nn.Module):
                    _model.eval()
                _model_type = 'pytorch'
                print("Model loaded (full model)")
            except:
                # If that fails, try loading as state dict
                checkpoint = torch.load(model_path, map_location=device)
                if isinstance(checkpoint, dict) and 'model' in checkpoint:
                    _model = checkpoint['model']
                    _model.eval()
                    _model_type = 'pytorch'
                elif isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
                    print("WARNING: State dict found. You need to define your model architecture.")
                    _model = checkpoint
                    _model_type = 'pytorch'
                else:
                    _model = checkpoint
                    _model_type = 'pytorch'
                print("Model loaded (checkpoint/state dict)")
        
        elif file_ext == '.onnx':
            # ONNX model - will need onnxruntime
            try:
                import onnxruntime as ort
                _model = ort.InferenceSession(model_path)
                _model_type = 'onnx'
                print("ONNX model loaded")
            except ImportError:
                raise ImportError("onnxruntime not installed. Install with: pip install onnxruntime")
        
        elif file_ext == '.h5':
            # TensorFlow/Keras model
            try:
                import tensorflow as tf
                _model = tf.keras.models.load_model(model_path)
                _model_type = 'tensorflow'
                print("TensorFlow/Keras model loaded")
            except ImportError:
                raise ImportError("TensorFlow not installed. Install with: pip install tensorflow")
        
        else:
            raise ValueError(f"Unsupported model format: {file_ext}")
        
        _model_path = model_path
        return _model
    
    except Exception as e:
        raise Exception(f"Error loading model: {str(e)}\n"
                       f"Please check:\n"
                       f"1. Model file format is correct\n"
                       f"2. Required libraries are installed\n"
                       f"3. Model architecture matches the saved model")

def get_model():
    """Get the loaded model"""
    return _model

def get_model_path_loaded():
    """Get the path of the loaded model"""
    return _model_path

def get_model_type():
    """Get the type of the loaded model"""
    return _model_type

