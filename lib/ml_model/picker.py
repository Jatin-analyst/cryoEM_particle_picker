"""
Universal ML model loader for CryoEM particle detection
Supports multiple model types: crYOLO, YOLO, DETR, etc.
"""

from pathlib import Path
from typing import Optional, Union
import torch

# Handle imports for both package and direct execution
try:
    from ..error_handling import ModelError
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from error_handling import ModelError

try:
    from ultralytics import YOLO
except ImportError:
    raise ImportError(
        "ultralytics package not found. Install with: pip install ultralytics"
    )

# Import crYOLO support
try:
    from .cryolo_picker import CrYOLOInferenceEngine
    CRYOLO_AVAILABLE = True
except ImportError:
    try:
        from cryolo_picker import CrYOLOInferenceEngine
        CRYOLO_AVAILABLE = True
    except ImportError:
        CRYOLO_AVAILABLE = False


# Global model cache for batch processing
_model_cache = {}


def load_model_cached(
    model_path: str = None,
    model_type: str = "cryolo",
    device: str = "cpu",
    validate: bool = True
) -> Union[CrYOLOInferenceEngine]:
    """
    Load crYOLO model with caching for batch processing.
    crYOLO is the primary model for CryoEM particle detection.
    
    Args:
        model_path: Path to crYOLO model weights (.h5 file) - auto-detected if None
        model_type: Model type (always 'cryolo' - other types deprecated)
        device: Target device ('cpu' or 'cuda')
        validate: Validate model compatibility before loading
        
    Returns:
        Loaded crYOLO inference engine
        
    Raises:
        ModelError: If crYOLO model cannot be loaded
    """
    global _model_cache
    
    # Use default crYOLO model if no path specified
    if model_path is None:
        model_path = get_default_model_path()
    
    # Force crYOLO as the primary model
    model_type = "cryolo"
    
    # Create cache key
    cache_key = f"{model_path}_{model_type}_{device}"
    
    # Return cached model if available
    if cache_key in _model_cache:
        return _model_cache[cache_key]
    
    # Load crYOLO model
    model = _load_cryolo_model(model_path, device)
    
    # Cache model
    _model_cache[cache_key] = model
    
    return model


def _detect_model_type(model_path: str) -> str:
    """Auto-detect model type from path or filename."""
    model_path_lower = model_path.lower()
    
    if 'cryolo' in model_path_lower or model_path_lower.endswith('.h5'):
        return 'cryolo'
    elif model_path_lower.endswith('.pt') or model_path_lower.startswith('yolo'):
        return 'yolo'
    else:
        # Default to YOLO for unknown types
        return 'yolo'


def _load_cryolo_model(model_path: str, device: str) -> CrYOLOInferenceEngine:
    """Load crYOLO model."""
    if not CRYOLO_AVAILABLE:
        raise ModelError(
            issue="crYOLO not available",
            details="crYOLO support is not installed",
            suggestion="Install crYOLO or use YOLO models instead"
        )
    
    try:
        # For crYOLO, model_path might be directory or specific file
        if model_path.endswith('.h5'):
            model_file = model_path
            config_file = model_path.replace('.h5', '.json')
        else:
            # Use default pretrained model
            model_file = None
            config_file = None
        
        engine = CrYOLOInferenceEngine(
            model_path=model_file,
            config_path=config_file,
            device='gpu' if device == 'cuda' else 'cpu',
            use_pretrained=True
        )
        
        return engine
        
    except Exception as e:
        raise ModelError(
            issue="crYOLO model loading failed",
            details=f"Error loading crYOLO model: {str(e)}",
            suggestion="Check crYOLO installation and model files"
        )


def _load_yolo_model(model_path: str, device: str, validate: bool) -> YOLO:
    """
    Load YOLOv8 model with caching for batch processing.
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
    Get path to default crYOLO model.
    crYOLO is the primary and preferred model for CryoEM particle detection.
    
    Returns:
        Path to crYOLO model (will be auto-downloaded if needed)
    """
    # crYOLO is the main model - always use it
    cryolo_dir = Path(__file__).parent / 'models' / 'cryolo'
    cryolo_model = cryolo_dir / 'general_model.h5'
    
    # Return crYOLO path (will be downloaded automatically if not exists)
    return str(cryolo_model)


def get_default_model_type() -> str:
    """
    Get the type of the default model.
    Always returns 'cryolo' as it's the primary model.
    
    Returns:
        Model type: 'cryolo'
    """
    return 'cryolo'
