# CryoEM Precision Tool - Library Structure

## Overview

This library provides the core functionality for ML-based particle picking and CTF estimation in CryoEM micrographs.

## Directory Structure

```
lib/
├── __init__.py                 # Main package initialization
├── data_models.py              # Core data structures (ParticleDetection, CTFParameters, MicrographResult)
├── error_handling.py           # Error categories, exit codes, and validation
├── logging_config.py           # Logging configuration
│
├── ml_model/                   # ML model architecture and inference
│   ├── picker.py              # ParticleCNN model definition
│   └── Inference.py           # FastInferenceEngine for batch inference
│
├── preprocessing/              # Micrograph preprocessing
│   ├── __init__.py
│   └── fast_normalize.py      # Memory-mapped loading, normalization, patch extraction
│
├── ctf/                        # CTF estimation
│   ├── __init__.py
│   └── estimation.py          # CTFEstimator with FFT-based analysis
│
├── postprocessing/             # Detection filtering and refinement
│   ├── __init__.py
│   └── filtering.py           # Confidence filtering, NMS, edge exclusion
│
├── storage/                    # External storage integration
│   ├── __init__.py
│   └── external_mounts.py     # StorageManager for NFS/Lustre/BeeGFS
│
└── utils/                      # Utility functions
    ├── __init__.py
    └── file_io.py             # STAR file writer, heatmap generation
```

## Error Handling

The library uses a structured error handling system with four exit codes:

- **Exit Code 1**: Input Validation Errors (invalid parameters, file format)
- **Exit Code 2**: File I/O Errors (cannot read/write files, storage issues)
- **Exit Code 3**: Model Errors (missing/corrupted model, incompatibility)
- **Exit Code 4**: Processing Errors (GPU memory, CTF estimation failures)

## Data Models

### ParticleDetection
Single particle detection with coordinates and confidence score.

### CTFParameters
CTF estimation results including defocus, astigmatism, and resolution metrics.

### MicrographResult
Complete processing results for one micrograph including particles and CTF parameters.

## Usage

```python
from lib import (
    ParticleDetection,
    CTFParameters,
    MicrographResult,
    setup_logging,
    validate_particle_size,
    validate_confidence_threshold
)

# Set up logging
logger = setup_logging(verbose=True)

# Validate parameters
validate_particle_size(200)  # Raises InputValidationError if invalid
validate_confidence_threshold(0.7)  # Raises InputValidationError if invalid
```

## Requirements

- Python 3.8+
- PyTorch 1.13+
- NumPy 1.24+
- mrcfile 1.5+
- Numba 0.58+
- Plotly 5.14+
- Seaborn 0.12+
