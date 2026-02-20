"""
Post-processing filters for particle detection
Confidence filtering, non-maximum suppression, and edge exclusion
"""

import numpy as np
from typing import Tuple
import numba


def filter_by_confidence(
    coords: np.ndarray,
    confidences: np.ndarray,
    threshold: float
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Filter particles by confidence threshold.
    
    Args:
        coords: Particle coordinates (N, 2) as [x, y]
        confidences: Confidence scores (N,)
        threshold: Minimum confidence (0.1-0.99)
        
    Returns:
        Filtered coords and confidences
    """
    # Create mask for particles above threshold
    mask = confidences >= threshold
    
    # Apply mask
    filtered_coords = coords[mask]
    filtered_confidences = confidences[mask]
    
    return filtered_coords, filtered_confidences


@numba.jit(nopython=True)
def _compute_distances(coords: np.ndarray) -> np.ndarray:
    """
    Compute pairwise distances between coordinates.
    Numba-accelerated for speed.
    
    Args:
        coords: Particle coordinates (N, 2)
        
    Returns:
        Distance matrix (N, N)
    """
    n = len(coords)
    distances = np.zeros((n, n), dtype=np.float32)
    
    for i in range(n):
        for j in range(i + 1, n):
            dx = coords[i, 0] - coords[j, 0]
            dy = coords[i, 1] - coords[j, 1]
            dist = np.sqrt(dx * dx + dy * dy)
            distances[i, j] = dist
            distances[j, i] = dist
    
    return distances


def non_maximum_suppression(
    coords: np.ndarray,
    confidences: np.ndarray,
    min_distance: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Remove overlapping detections, keeping highest confidence.
    Uses vectorized operations for speed.
    
    Args:
        coords: Particle coordinates (N, 2) as [x, y]
        confidences: Confidence scores (N,)
        min_distance: Minimum separation distance in pixels
        
    Returns:
        Filtered coords and confidences
    """
    if len(coords) == 0:
        return coords, confidences
    
    # Sort by confidence (descending)
    order = np.argsort(confidences)[::-1]
    
    # Track which detections to keep
    keep = []
    suppressed = np.zeros(len(coords), dtype=bool)
    
    # Compute all pairwise distances once
    distances = _compute_distances(coords)
    
    # Process in order of confidence
    for idx in order:
        if suppressed[idx]:
            continue
        
        # Keep this detection
        keep.append(idx)
        
        # Suppress nearby detections with lower confidence
        nearby = distances[idx] < min_distance
        suppressed[nearby] = True
        suppressed[idx] = False  # Don't suppress self
    
    # Return kept detections
    keep = np.array(keep)
    return coords[keep], confidences[keep]


def apply_edge_exclusion(
    coords: np.ndarray,
    confidences: np.ndarray,
    image_shape: Tuple[int, int],
    exclusion_distance: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Exclude particles near image edges.
    
    Args:
        coords: Particle coordinates (N, 2) as [x, y]
        confidences: Confidence scores (N,)
        image_shape: (height, width) of micrograph
        exclusion_distance: Distance from edge to exclude (pixels)
        
    Returns:
        Filtered coords and confidences
    """
    if exclusion_distance <= 0:
        return coords, confidences
    
    h, w = image_shape
    
    # Create mask for particles not near edges
    valid = (
        (coords[:, 0] >= exclusion_distance) &
        (coords[:, 0] < w - exclusion_distance) &
        (coords[:, 1] >= exclusion_distance) &
        (coords[:, 1] < h - exclusion_distance)
    )
    
    # Apply mask
    filtered_coords = coords[valid]
    filtered_confidences = confidences[valid]
    
    return filtered_coords, filtered_confidences
