"""
YOLOv8n-based particle detection for CryoEM micrographs
Lightweight object detection with pretrained weights
"""

from pathlib import Path
from typing import Optional
import torch

from ..error_handling import ModelError

try:
    from ultralytics import YOLO
except ImportError:
    raise ImportError(
        "ultralytics package not found. Install with: pip install ultralytics"
    )


# Global model cache for batch processing
_model_cache = {}


def load_model_cached(
    model_path: str,
    device: str = "cpu",
    validate: bool = True
) -> YOLO:
    """
    Load YOLOv8n model with caching for batch processing.
    Model is loaded once and reused for subsequent calls.
    
    Args:
        model_path: Path to model weights (.pt file) or 'yolov8n.pt' for pretrained
        device: Target device ('cpu' or 'cuda')
        validate: Validate model compatibility before loading
        
    Returns:
        Loaded YOLO model
        
    Raises:
        ModelError: If model file is missing, corrupted, or incompatible
    """
    global _model_cache
    
    # Create cache key
    cache_key = f"{model_path}_{device}"
    
    # Return cached model if available
    if cache_key in _model_cache:
        return _model_cache[cache_key]
    
    # Check if using pretrained or custom weights
    model_path_obj = Path(model_path)
    
    # If path doesn't exist and it's not a standard YOLO model name, raise error
    if not model_path_obj.exists() and not model_path.startswith('yolov8'):
        raise ModelError(
            issue="Model file not found",
            details=f"Cannot find model file: {model_path}",
            suggestion="Check that the model path is correct or use 'yolov8n.pt' for pretrained model"
        )
    
    try:
        # Load YOLO model
        model = YOLO(model_path)
        
        # Move to device
        model.to(device)
        
        # Validate model if requested
        if validate:
            _validate_model_compatibility(model, device)
        
        # Cache model
        _model_cache[cache_key] = model
        
        return model
        
    except RuntimeError as e:
        raise ModelError(
            issue="Model loading failed",
            details=f"Error loading model from {model_path}: {str(e)}",
            suggestion="Check that the model file is not corrupted and is compatible with ultralytics"
        )
    except Exception as e:
        raise ModelError(
            issue="Unexpected model error",
            details=f"Unexpected error loading model: {str(e)}",
            suggestion="Check that the model file is valid and ultralytics is properly installed"
        )


def _validate_model_compatibility(model: YOLO, device: str) -> None:
    """
    Validate that model is compatible with expected input/output format.
    
    Args:
        model: Loaded YOLO model
        device: Device model is on
        
    Raises:
        ModelError: If model is incompatible
    """
    try:
        # Check model type
        if not hasattr(model, 'predict'):
            raise ModelError(
                issue="Invalid model type",
                details="Model does not have predict method",
                suggestion="Use a valid YOLOv8 model"
            )
        
        # Check that model is in detection mode (not segmentation or classification)
        model_type = str(type(model.model)).lower()
        if 'segment' in model_type or 'classify' in model_type:
            raise ModelError(
                issue="Wrong model task type",
                details=f"Expected detection model, got {model_type}",
                suggestion="Use YOLOv8 detection model (yolov8n.pt, not yolov8n-seg.pt or yolov8n-cls.pt)"
            )
            
    except ModelError:
        raise
    except Exception as e:
        raise ModelError(
            issue="Model validation failed",
            details=f"Error during model validation: {str(e)}",
            suggestion="Check that the model is a valid YOLOv8 detection model"
        )


def get_default_model_path() -> str:
    """
    Get path to default pretrained YOLOv8n model.
    
    Returns:
        Path to default model or 'yolov8n.pt' to download pretrained
    """
    # Check if we have a fine-tuned model in the weights directory
    weights_dir = Path(__file__).parent / 'weights'
    finetuned_path = weights_dir / 'yolov8n_cryoem.pt'
    
    if finetuned_path.exists():
        return str(finetuned_path)
    
    # Otherwise use pretrained YOLOv8n (will be downloaded automatically)
    return 'yolov8n.pt'
