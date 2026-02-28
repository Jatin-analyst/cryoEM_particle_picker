"""
Preprocessing module for CryoEM micrographs
Handles file loading, normalization, and patch extraction
"""

try:
    from .fast_normalize import (
        load_micrograph_mmap,
        normalize_micrograph,
        extract_patches
    )
except ImportError:
    # Fallback for direct execution
    from fast_normalize import (
        load_micrograph_mmap,
        normalize_micrograph,
        extract_patches
    )

__all__ = [
    'load_micrograph_mmap',
    'normalize_micrograph',
    'extract_patches'
]
