"""
crYOLO-based inference engine for CryoEM particle detection
Optimized for CryoEM data with crYOLO as the primary model
"""

import torch
import numpy as np
from typing import Tuple, Optional
from PIL import Image
from pathlib import Path

# Import crYOLO support as primary
try:
    from .cryolo_picker import CrYOLOInferenceEngine
    CRYOLO_AVAILABLE = True
except ImportError:
    try:
        from cryolo_picker import CrYOLOInferenceEngine
        CRYOLO_AVAILABLE = True
    except ImportError:
        CRYOLO_AVAILABLE = False

# Keep YOLO as fallback only
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False


class CryoEMInferenceEngine:
    """
    CryoEM-optimized inference engine using crYOLO as the primary model.
    
    Model Priority:
    1. crYOLO (primary - best for CryoEM)
    2. Enhanced blob detection (fallback)
    
    Performance:
    - crYOLO: ~1-2 seconds for 4k x 4k micrograph
    - Superior accuracy on CryoEM particles
    - Handles various particle types and sizes
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = 'cpu',
        force_cryolo: bool = True
    ):
        """
        Initialize crYOLO-based inference engine.
        
        Args:
            model_path: Path to crYOLO model (.h5 file) - auto-detected if None
            device: Computation device ('cpu' or 'cuda')
            force_cryolo: Always try to use crYOLO (recommended)
        """
        self.device = device
        self.force_cryolo = force_cryolo
        
        # Initialize crYOLO as primary model
        self.cryolo_engine = None
        self.fallback_engine = None
        
        self._setup_primary_model(model_path)
    
    def _setup_primary_model(self, model_path: Optional[str]):
        """Setup crYOLO as the primary model."""
        print("🔬 Initializing CryoEM Particle Picker with crYOLO...")
        
        try:
            # Initialize crYOLO engine
            self.cryolo_engine = CrYOLOInferenceEngine(
                model_path=model_path,
                config_path=None,  # Auto-detected
                device=self.device,
                use_pretrained=True
            )
            print("✅ crYOLO engine initialized successfully")
            
        except Exception as e:
            print(f"⚠️  crYOLO initialization failed: {str(e)}")
            if self.force_cryolo:
                print("🔄 Setting up crYOLO fallback implementation...")
                # Still use crYOLO fallback which is better than YOLO for CryoEM
                self.cryolo_engine = CrYOLOInferenceEngine(
                    model_path=None,
                    config_path=None,
                    device=self.device,
                    use_pretrained=True
                )
            else:
                self.cryolo_engine = None
    
    def predict_micrograph(
        self,
        micrograph: np.ndarray,
        particle_size: int,
        stride: Optional[int] = None,
        conf_threshold: float = 0.3
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict particle locations using crYOLO.
        
        Args:
            micrograph: Normalized micrograph (H, W)
            particle_size: Particle diameter in pixels
            stride: Not used for crYOLO (kept for API compatibility)
            conf_threshold: Confidence threshold for detections (crYOLO optimized: 0.3)
            
        Returns:
            coords: Particle coordinates (N, 2) as [x, y] (center points)
            confidences: Confidence scores (N,)
        """
        # Use crYOLO as primary method
        if self.cryolo_engine is not None:
            try:
                coords, confidences = self.cryolo_engine.predict_micrograph(
                    micrograph=micrograph,
                    particle_size=particle_size,
                    conf_threshold=conf_threshold,
                    distance_threshold=particle_size
                )
                
                print(f"🎯 crYOLO detected {len(coords)} particles")
                return coords, confidences
                
            except Exception as e:
                print(f"⚠️  crYOLO prediction failed: {str(e)}")
                print("🔄 Using enhanced fallback detection...")
        
        # Enhanced fallback detection (still CryoEM-optimized)
        return self._enhanced_fallback_detection(micrograph, particle_size, conf_threshold)
    
    def _enhanced_fallback_detection(
        self,
        micrograph: np.ndarray,
        particle_size: int,
        conf_threshold: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Enhanced fallback detection optimized for CryoEM data.
        Uses advanced image processing techniques.
        """
        from scipy import ndimage
        from skimage.feature import blob_log, peak_local_maxima
        from skimage.filters import gaussian, difference_of_gaussians
        from skimage.morphology import white_tophat, disk
        
        print("🔍 Using enhanced CryoEM-optimized detection...")
        
        # Normalize micrograph
        micrograph_norm = (micrograph - micrograph.mean()) / micrograph.std()
        
        # Multi-scale detection approach
        coords_all = []
        confidences_all = []
        
        # Method 1: Difference of Gaussians (DoG) - excellent for particles
        sigma1 = particle_size / 8.0
        sigma2 = particle_size / 4.0
        dog_filtered = difference_of_gaussians(micrograph_norm, sigma1, sigma2)
        
        # Find local maxima in DoG response
        coordinates = peak_local_maxima(
            dog_filtered,
            min_distance=int(particle_size * 0.8),
            threshold_abs=np.std(dog_filtered) * 2,
            num_peaks=1000
        )
        
        if len(coordinates) > 0:
            coords_dog = np.array(coordinates)[:, [1, 0]]  # Convert to [x, y]
            
            # Calculate confidence based on DoG response
            confidences_dog = []
            for y, x in coordinates:
                region_size = int(particle_size // 4)
                y1, y2 = max(0, y-region_size), min(dog_filtered.shape[0], y+region_size)
                x1, x2 = max(0, x-region_size), min(dog_filtered.shape[1], x+region_size)
                
                region = dog_filtered[y1:y2, x1:x2]
                if region.size > 0:
                    confidence = min(1.0, max(0.0, (region.max() - region.mean()) / region.std()))
                else:
                    confidence = 0.1
                confidences_dog.append(confidence)
            
            coords_all.extend(coords_dog)
            confidences_all.extend(confidences_dog)
        
        # Method 2: Blob detection with LOG
        min_sigma = particle_size / 10.0
        max_sigma = particle_size / 3.0
        
        blobs = blob_log(
            micrograph_norm,
            min_sigma=min_sigma,
            max_sigma=max_sigma,
            num_sigma=15,
            threshold=0.05,
            overlap=0.5
        )
        
        if len(blobs) > 0:
            coords_blob = blobs[:, [1, 0]]  # Convert to [x, y]
            confidences_blob = np.clip(blobs[:, 2] / max_sigma, 0.1, 1.0)
            
            coords_all.extend(coords_blob)
            confidences_all.extend(confidences_blob)
        
        # Combine and filter results
        if len(coords_all) == 0:
            return np.array([]).reshape(0, 2), np.array([])
        
        coords = np.array(coords_all)
        confidences = np.array(confidences_all)
        
        # Filter by confidence threshold
        valid_mask = confidences >= conf_threshold
        coords = coords[valid_mask]
        confidences = confidences[valid_mask]
        
        # Remove duplicates (particles detected by multiple methods)
        if len(coords) > 1:
            coords, confidences = self._remove_duplicates(coords, confidences, particle_size * 0.5)
        
        print(f"   ✅ Enhanced detection found {len(coords)} particles")
        
        return coords, confidences
    
    def _remove_duplicates(
        self,
        coords: np.ndarray,
        confidences: np.ndarray,
        min_distance: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Remove duplicate detections that are too close together."""
        if len(coords) <= 1:
            return coords, confidences
        
        # Calculate pairwise distances
        from scipy.spatial.distance import pdist, squareform
        distances = squareform(pdist(coords))
        
        # Find pairs that are too close
        close_pairs = np.where((distances < min_distance) & (distances > 0))
        
        # Keep the detection with higher confidence
        to_remove = set()
        for i, j in zip(close_pairs[0], close_pairs[1]):
            if i not in to_remove and j not in to_remove:
                if confidences[i] < confidences[j]:
                    to_remove.add(i)
                else:
                    to_remove.add(j)
        
        # Remove duplicates
        keep_mask = np.ones(len(coords), dtype=bool)
        keep_mask[list(to_remove)] = False
        
        return coords[keep_mask], confidences[keep_mask]
    
    def predict_batch(self, images: list, particle_sizes: list) -> list:
        """
        Batch inference on multiple micrographs.
        
        Args:
            images: List of micrographs (each H, W)
            particle_sizes: List of particle sizes for each image
            
        Returns:
            List of (coords, confidences) tuples
        """
        results = []
        
        for img, psize in zip(images, particle_sizes):
            coords, confs = self.predict_micrograph(img, psize)
            results.append((coords, confs))
        
        return results


# Alias for backward compatibility
FastInferenceEngine = CryoEMInferenceEngine
