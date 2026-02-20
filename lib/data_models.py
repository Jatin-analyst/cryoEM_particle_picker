"""
Data models for CryoEM Precision Tool
Defines core data structures used throughout the system
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np


@dataclass
class ParticleDetection:
    """Single particle detection result."""
    x: float  # X coordinate in pixels
    y: float  # Y coordinate in pixels
    confidence: float  # Confidence score (0.0-1.0)
    
    def __post_init__(self):
        """Validate particle detection data."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be in [0.0, 1.0], got {self.confidence}")


@dataclass
class CTFParameters:
    """CTF estimation results."""
    defocus_u: float  # Defocus in U direction (micrometers)
    defocus_v: float  # Defocus in V direction (micrometers)
    astigmatism: float  # Astigmatism (Angstroms)
    astigmatism_angle: float  # Astigmatism angle (degrees)
    fit_resolution: float  # CTF fit resolution (Angstroms)
    max_resolution: float  # Maximum resolution from Thon rings (Angstroms)
    fit_quality: float  # Quality of fit (0.0-1.0)
    
    def average_defocus(self) -> float:
        """Calculate average defocus."""
        return (self.defocus_u + self.defocus_v) / 2.0
    
    def is_valid(self) -> bool:
        """Check if parameters are within valid ranges."""
        avg_defocus = self.average_defocus()
        return (
            0.5 <= avg_defocus <= 3.5 and
            self.astigmatism < 500.0 and
            4.5 <= self.fit_resolution <= 6.0 and
            3.4 <= self.max_resolution <= 5.0
        )


@dataclass
class MicrographResult:
    """Complete results for one micrograph."""
    micrograph_path: str
    particles: List[ParticleDetection]
    ctf_parameters: Optional[CTFParameters]
    processing_time: float  # Seconds
    image_shape: Tuple[int, int]
    
    def particle_count(self) -> int:
        """Return number of detected particles."""
        return len(self.particles)
    
    def mean_confidence(self) -> float:
        """Calculate mean confidence score."""
        if not self.particles:
            return 0.0
        return np.mean([p.confidence for p in self.particles])
