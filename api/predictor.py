"""
Prediction Module
Handles image preprocessing and model inference
"""
import torch
import numpy as np
from PIL import Image
from typing import Dict, List, Optional
from .model_loader import get_model, get_model_type

def preprocess_image(image: Image.Image, target_size: tuple = (640, 640)) -> np.ndarray:
    """
    Preprocess image for model input
    
    Args:
        image: PIL Image
        target_size: Target size (width, height)
    
    Returns:
        Preprocessed image array
    """
    # Resize image
    image = image.resize(target_size, Image.LANCZOS)
    
    # Convert to numpy array
    img_array = np.array(image)
    
    # Normalize to [0, 1]
    img_array = img_array.astype(np.float32) / 255.0
    
    # Convert to CHW format (if needed)
    if len(img_array.shape) == 3:
        img_array = np.transpose(img_array, (2, 0, 1))
    
    # Add batch dimension
    img_array = np.expand_dims(img_array, axis=0)
    
    return img_array

def postprocess_predictions(
    predictions: any,
    original_size: tuple,
    target_size: tuple = (640, 640),
    confidence_threshold: float = 0.5
) -> Dict[str, List]:
    """
    Postprocess model predictions to extract bounding boxes and classes
    
    Args:
        predictions: Raw model predictions
        original_size: Original image size (width, height)
        target_size: Model input size (width, height)
        confidence_threshold: Minimum confidence for detections
    
    Returns:
        Dictionary with boxes, classes, and confidences
    """
    model = get_model()
    
    if model is None:
        raise ValueError("Model not loaded. Call load_model() first.")
    
    # This is a template - you need to adapt based on your model's output format
    # Common formats:
    # 1. YOLO: [batch, num_detections, 6] where 6 = [x, y, w, h, conf, class]
    # 2. Faster R-CNN: dict with 'boxes', 'labels', 'scores'
    # 3. Custom: depends on your model
    
    boxes = []
    classes = []
    confidences = []
    
    # Scale factors for converting back to original image size
    scale_x = original_size[0] / target_size[0]
    scale_y = original_size[1] / target_size[1]
    
    # Example for PyTorch models (adjust based on your model)
    if isinstance(predictions, torch.Tensor):
        predictions = predictions.cpu().numpy()
    
    if isinstance(predictions, dict):
        # Handle dictionary outputs (common in PyTorch detection models)
        if 'boxes' in predictions:
            pred_boxes = predictions['boxes']
            pred_scores = predictions.get('scores', [])
            pred_labels = predictions.get('labels', [])
            
            for box, score, label in zip(pred_boxes, pred_scores, pred_labels):
                if score >= confidence_threshold:
                    # Convert box format [x1, y1, x2, y2] and scale
                    x1, y1, x2, y2 = box[:4]
                    x1 *= scale_x
                    y1 *= scale_y
                    x2 *= scale_x
                    y2 *= scale_y
                    
                    boxes.append([float(x1), float(y1), float(x2), float(y2)])
                    confidences.append(float(score))
                    classes.append(f"weed_class_{int(label)}")  # Update with your class names
    
    elif isinstance(predictions, np.ndarray):
        # Handle numpy array outputs (e.g., YOLO format)
        # Shape: [num_detections, 6] where 6 = [x, y, w, h, conf, class]
        if len(predictions.shape) == 2 and predictions.shape[1] >= 6:
            for pred in predictions:
                conf = pred[4]
                if conf >= confidence_threshold:
                    x, y, w, h = pred[0:4]
                    # Convert center+wh to x1y1x2y2
                    x1 = (x - w/2) * scale_x
                    y1 = (y - h/2) * scale_y
                    x2 = (x + w/2) * scale_x
                    y2 = (y + h/2) * scale_y
                    
                    boxes.append([float(x1), float(y1), float(x2), float(y2)])
                    confidences.append(float(conf))
                    classes.append(f"weed_class_{int(pred[5])}")  # Update with your class names
    
    # TODO: Add your specific model's postprocessing logic here
    # You need to know:
    # 1. What format does your model output?
    # 2. What are your class names?
    # 3. How are bounding boxes formatted?
    
    return {
        "boxes": boxes,
        "classes": classes,
        "confidences": confidences
    }

def predict_image(image: Image.Image) -> Optional[Dict[str, List]]:
    """
    Main prediction function
    
    Args:
        image: PIL Image to predict on
    
    Returns:
        Dictionary with predictions or None if error
    """
    try:
        model = get_model()
        model_type = get_model_type()
        
        if model is None:
            raise ValueError("Model not loaded")
        
        original_size = image.size  # (width, height)
        
        # Handle YOLOv8 models
        if model_type == 'yolo':
            # YOLOv8 models handle preprocessing internally
            results = model.predict(image, conf=0.25, verbose=False)
            
            boxes = []
            classes = []
            confidences = []
            
            # YOLOv8 returns a list of Results objects
            if len(results) > 0:
                result = results[0]
                
                # Get class names from model
                class_names = result.names if hasattr(result, 'names') else {}
                
                # Extract boxes, confidences, and classes
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes_data = result.boxes.xyxy.cpu().numpy()  # [x1, y1, x2, y2]
                    confidences_data = result.boxes.conf.cpu().numpy()
                    classes_data = result.boxes.cls.cpu().numpy().astype(int)
                    
                    for box, conf, cls_id in zip(boxes_data, confidences_data, classes_data):
                        boxes.append([float(box[0]), float(box[1]), float(box[2]), float(box[3])])
                        confidences.append(float(conf))
                        # Use class name if available, otherwise use class ID
                        class_name = class_names.get(cls_id, f"weed_class_{cls_id}")
                        classes.append(class_name)
            
            return {
                "boxes": boxes,
                "classes": classes,
                "confidences": confidences
            }
        
        # Handle other model types (PyTorch, TensorFlow, ONNX)
        # Preprocess image
        processed_image = preprocess_image(image)
        
        # Convert to tensor if using PyTorch
        if isinstance(model, torch.nn.Module):
            device = next(model.parameters()).device
            input_tensor = torch.from_numpy(processed_image).to(device)
            
            # Run inference
            with torch.no_grad():
                predictions = model(input_tensor)
        elif hasattr(model, 'run'):  # ONNX model
            input_name = model.get_inputs()[0].name
            predictions = model.run(None, {input_name: processed_image})[0]
        else:
            # TensorFlow or other
            predictions = model.predict(processed_image)
        
        # Postprocess predictions
        results = postprocess_predictions(predictions, original_size)
        
        return results
    
    except Exception as e:
        print(f"Error in prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

