"""
CryoEM Precision Tool Library
Main package initialization
"""

from .data_models import ParticleDetection, CTFParameters, MicrographResult
from .error_handling import (
    ExitCode,
    CryoEMError,
    InputValidationError,
    FileIOError,
    ModelError,
    ProcessingError,
    handle_error,
    validate_particle_size,
    validate_confidence_threshold,
    validate_file_exists
)
from .logging_config import setup_logging, get_logger
from .batch_processing import BatchProcessor, BatchResult, BatchSummary

__version__ = '2.0.0'

__all__ = [
    # Data models
    'ParticleDetection',
    'CTFParameters',
    'MicrographResult',
    
    # Error handling
    'ExitCode',
    'CryoEMError',
    'InputValidationError',
    'FileIOError',
    'ModelError',
    'ProcessingError',
    'handle_error',
    'validate_particle_size',
    'validate_confidence_threshold',
    'validate_file_exists',
    
    # Logging
    'setup_logging',
    'get_logger',
    
    # Batch processing
    'BatchProcessor',
    'BatchResult',
    'BatchSummary',
    
    # Version
    '__version__'
]
