"""
Fast preprocessing for CryoEM micrographs
Memory-mapped loading, Numba-accelerated normalization, and patch extraction
"""

import numpy as np
import mrcfile
from pathlib import Path
from typing import Tuple
import numba

# Handle imports for both package and direct execution
try:
    from ..error_handling import InputValidationError, FileIOError
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from error_handling import InputValidationError, FileIOError


def load_micrograph_mmap(filepath: str) -> np.ndarray:
    """
    Load micrograph using memory-mapped I/O.
    Does not load entire file into RAM, enabling efficient processing of large files.
    
    Args:
        filepath: Path to MRC file
        
    Returns:
        Memory-mapped array (not loaded into RAM)
        
    Raises:
        InputValidationError: If file is not valid MRC format
        FileIOError: If file cannot be read
    """
    filepath_obj = Path(filepath)
    
    # Check file exists
    if not filepath_obj.exists():
        raise FileIOError(
            issue="Micrograph file not found",
            details=f"Cannot find file: {filepath}",
            suggestion="Check that the file path is correct and the file exists"
        )
    
    # Check file extension (.st files are also MRC format)
    if filepath_obj.suffix.lower() not in ['.mrc', '.mrcs', '.st']:
        raise InputValidationError(
            issue="Invalid file format",
            details=f"Expected MRC format (.mrc, .mrcs, or .st), got {filepath_obj.suffix}",
            suggestion="Provide a micrograph file in MRC format (.mrc, .mrcs, or .st)"
        )
    
    try:
        # Open with memory mapping (permissive mode for compatibility)
        with mrcfile.mmap(filepath, mode='r', permissive=True) as mrc:
            # Get data shape
            data_shape = mrc.data.shape
            
            # Handle 3D tomograms (.st files) - extract middle slice
            if len(data_shape) == 3:
                middle_slice = data_shape[0] // 2
                print(f"Note: 3D tomogram detected ({data_shape}), extracting middle slice {middle_slice}")
                return np.array(mrc.data[middle_slice, :, :], dtype=np.float32)
            
            # Validate dimensions (support 2D micrographs up to 8192x8192)
            if len(data_shape) != 2:
                raise InputValidationError(
                    issue="Invalid micrograph dimensions",
                    details=f"Expected 2D micrograph or 3D tomogram, got shape {data_shape}",
                    suggestion="Provide a 2D micrograph or 3D tomogram"
                )
            
            if data_shape[0] > 8192 or data_shape[1] > 8192:
                raise InputValidationError(
                    issue="Micrograph too large",
                    details=f"Maximum supported dimensions are 8192x8192, got {data_shape}",
                    suggestion="Resize the micrograph or process in smaller tiles"
                )
            
            # Return copy as float32 for processing
            # Note: We make a copy here to avoid issues with memory-mapped files
            # For truly large files, consider processing in tiles
            return np.array(mrc.data, dtype=np.float32)
            
    except (OSError, IOError) as e:
        raise FileIOError(
            issue="Cannot read micrograph file",
            details=f"Error reading {filepath}: {str(e)}",
            suggestion="Check file permissions and ensure the file is not corrupted"
        )
    except ValueError as e:
        raise InputValidationError(
            issue="Corrupted MRC file",
            details=f"File {filepath} appears to be corrupted: {str(e)}",
            suggestion="Try re-downloading or re-generating the micrograph file"
        )


@numba.jit(nopython=True, parallel=True)
def normalize_micrograph(data: np.ndarray) -> np.ndarray:
    """
    Fast normalization to zero mean and unit variance.
    Uses Numba JIT compilation for speed.
    
    Args:
        data: Raw micrograph data (2D array)
        
    Returns:
        Normalized micrograph (zero mean, unit variance)
    """
    # Flatten for statistics calculation
    flat_data = data.ravel()
    
    # Calculate mean and std
    mean = np.mean(flat_data)
    std = np.std(flat_data)
    
    # Avoid division by zero
    if std < 1e-10:
        std = 1.0
    
    # Normalize
    normalized = (data - mean) / std
    
    return normalized


def extract_patches(
    micrograph: np.ndarray,
    patch_size: int,
    stride: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract overlapping patches for inference.
    
    Args:
        micrograph: Normalized micrograph (H, W)
        patch_size: Size of each square patch
        stride: Step size between patches
        
    Returns:
        patches: Array of patches (N, 1, patch_size, patch_size)
        positions: Array of patch center positions (N, 2) as [x, y]
    """
    h, w = micrograph.shape
    
    # Calculate number of patches
    n_patches_y = (h - patch_size) // stride + 1
    n_patches_x = (w - patch_size) // stride + 1
    
    # Pre-allocate arrays
    n_patches = n_patches_y * n_patches_x
    patches = np.zeros((n_patches, 1, patch_size, patch_size), dtype=np.float32)
    positions = np.zeros((n_patches, 2), dtype=np.float32)
    
    idx = 0
    for i in range(n_patches_y):
        for j in range(n_patches_x):
            # Calculate patch boundaries
            y_start = i * stride
            x_start = j * stride
            y_end = y_start + patch_size
            x_end = x_start + patch_size
            
            # Handle edge cases (ensure we don't go out of bounds)
            if y_end > h:
                y_start = h - patch_size
                y_end = h
            if x_end > w:
                x_start = w - patch_size
                x_end = w
            
            # Extract patch
            patch = micrograph[y_start:y_end, x_start:x_end]
            patches[idx, 0, :, :] = patch
            
            # Store center position
            center_x = x_start + patch_size // 2
            center_y = y_start + patch_size // 2
            positions[idx] = [center_x, center_y]
            
            idx += 1
    
    return patches[:idx], positions[:idx]
