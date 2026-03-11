"""
Input Validator for CryoEM Interactive Visualization
Orchestrates all validation checks and collects errors/warnings
"""

import os
import numpy as np
from typing import Tuple
from .validation_result import ValidationResult
from .file_format_detector import FileFormatDetector
from .error_reporter import ErrorReporter


class InputValidator:
    """Coordinate all validation checks and collect errors/warnings."""
    
    def __init__(self, micrograph_path: str, star_path: str):
        """
        Initialize validator with input file paths.
        
        Args:
            micrograph_path: Path to micrograph file
            star_path: Path to STAR file
        """
        self.micrograph_path = micrograph_path
        self.star_path = star_path
        self.result = ValidationResult()
    
    def validate_all(self) -> ValidationResult:
        """
        Run all validation checks.
        
        Returns:
            ValidationResult with all errors and warnings
        """
        self.check_duplicate_files()
        self.check_file_formats()
        self.check_micrograph_validity()
        self.check_star_validity()
        return self.result
    
    def check_duplicate_files(self):
        """Validate that micrograph and STAR are different files."""
        try:
            # Resolve to absolute paths to handle symlinks and relative paths
            micrograph_real = os.path.realpath(self.micrograph_path)
            star_real = os.path.realpath(self.star_path)
            
            if micrograph_real == star_real:
                # Check if it's a Galaxy dataset issue
                if 'dataset_' in os.path.basename(micrograph_real):
                    dataset_id = os.path.basename(micrograph_real)
                    message, suggestion = ErrorReporter.get_error_template(
                        'galaxy_duplicate_dataset',
                        dataset_id=dataset_id
                    )
                    error_msg = ErrorReporter.format_error(message, suggestion)
                    error_msg += f"\n   File: {micrograph_real}"
                else:
                    message, suggestion = ErrorReporter.get_error_template('duplicate_files')
                    error_msg = ErrorReporter.format_error(message, suggestion)
                    error_msg += f"\n   File: {micrograph_real}"
                
                self.result.add_error(error_msg)
        except (IOError, OSError) as e:
            # If we can't resolve paths, continue with other checks
            pass
    
    def check_file_formats(self):
        """Detect and validate file formats."""
        # Detect micrograph format
        micrograph_info = FileFormatDetector.detect_format(self.micrograph_path)
        
        # Check if micrograph is actually a STAR file
        if micrograph_info.format_type == 'star':
            message, suggestion = ErrorReporter.get_error_template(
                'wrong_format_micrograph',
                detected='STAR coordinate'
            )
            error_msg = ErrorReporter.format_error(message, suggestion)
            error_msg += f"\n   {ErrorReporter.format_file_info(self.micrograph_path, 'STAR format', 'MRC/MRCS/ST format')}"
            self.result.add_error(error_msg)
        
        # Detect STAR format
        star_info = FileFormatDetector.detect_format(self.star_path)
        
        # Check if STAR is actually an MRC file
        if star_info.format_type == 'mrc':
            message, suggestion = ErrorReporter.get_error_template(
                'wrong_format_star',
                detected='MRC micrograph'
            )
            error_msg = ErrorReporter.format_error(message, suggestion)
            error_msg += f"\n   {ErrorReporter.format_file_info(self.star_path, 'MRC format', 'STAR format')}"
            self.result.add_error(error_msg)
    
    def check_micrograph_validity(self):
        """Validate micrograph file can be loaded."""
        try:
            import mrcfile
            
            # Check if file exists and has size
            if not os.path.exists(self.micrograph_path):
                error_msg = ErrorReporter.format_error(
                    f"Micrograph file not found: {self.micrograph_path}",
                    "Please verify the file path and try again."
                )
                self.result.add_error(error_msg)
                return
            
            file_size = os.path.getsize(self.micrograph_path)
            if file_size == 0:
                message, suggestion = ErrorReporter.get_error_template('empty_micrograph')
                error_msg = ErrorReporter.format_error(message, suggestion)
                error_msg += f"\n   File: {self.micrograph_path}"
                self.result.add_error(error_msg)
                return
            
            # Try to open with mrcfile
            try:
                with mrcfile.open(self.micrograph_path, mode='r', permissive=True) as mrc:
                    data = mrc.data
                    
                    if data is None:
                        message, suggestion = ErrorReporter.get_error_template('empty_micrograph')
                        error_msg = ErrorReporter.format_error(message, suggestion)
                        error_msg += f"\n   File: {self.micrograph_path}"
                        error_msg += f"\n   Size: {file_size} bytes"
                        self.result.add_error(error_msg)
            except Exception as e:
                error_msg = ErrorReporter.format_error(
                    f"Failed to open micrograph file: {os.path.basename(self.micrograph_path)}",
                    "Please verify the file is a valid MRC/MRCS/ST format."
                )
                error_msg += f"\n   File: {self.micrograph_path}"
                error_msg += f"\n   Error: {str(e)}"
                self.result.add_error(error_msg)
        
        except ImportError:
            # mrcfile not available, skip this check
            pass
    
    def check_star_validity(self):
        """Validate STAR file structure and content."""
        try:
            # Check if file exists
            if not os.path.exists(self.star_path):
                error_msg = ErrorReporter.format_error(
                    f"STAR file not found: {self.star_path}",
                    "Please verify the file path and try again."
                )
                self.result.add_error(error_msg)
                return
            
            # Check if file is empty
            file_size = os.path.getsize(self.star_path)
            if file_size == 0:
                message, suggestion = ErrorReporter.get_error_template('empty_star')
                error_msg = ErrorReporter.format_error(message, suggestion)
                error_msg += f"\n   File: {self.star_path}"
                self.result.add_error(error_msg)
                return
            
            # Try to parse STAR file
            try:
                with open(self.star_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # File is binary, not a text STAR file
                message, suggestion = ErrorReporter.get_error_template(
                    'wrong_format_star',
                    detected='binary'
                )
                error_msg = ErrorReporter.format_error(message, suggestion)
                error_msg += f"\n   File: {self.star_path}"
                error_msg += f"\n   The file appears to be binary data, not a text STAR file."
                self.result.add_error(error_msg)
                return
            
            # Check for data loop
            if 'loop_' not in content:
                message, suggestion = ErrorReporter.get_error_template('no_data_loop')
                error_msg = ErrorReporter.format_error(message, suggestion)
                error_msg += f"\n   File: {self.star_path}"
                self.result.add_error(error_msg)
                return
            
            # Try to parse coordinates
            coords = []
            in_data = False
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('loop_'):
                    in_data = True
                    continue
                if in_data and line and not line.startswith('_'):
                    parts = line.split()
                    if len(parts) >= 3:
                        coords.append(parts[:3])
                    elif len(parts) > 0:
                        # Invalid row with too few columns
                        message, suggestion = ErrorReporter.get_error_template(
                            'invalid_star_columns',
                            n=len(parts)
                        )
                        error_msg = ErrorReporter.format_error(message, suggestion)
                        error_msg += f"\n   File: {self.star_path}"
                        error_msg += f"\n   Line: {line}"
                        self.result.add_error(error_msg)
                        return
            
            if len(coords) == 0:
                message, suggestion = ErrorReporter.get_error_template('no_particles')
                error_msg = ErrorReporter.format_error(message, suggestion)
                error_msg += f"\n   File: {self.star_path}"
                self.result.add_error(error_msg)
        
        except (IOError, OSError) as e:
            error_msg = ErrorReporter.format_error(
                f"Failed to read STAR file: {os.path.basename(self.star_path)}",
                "Please verify the file is accessible and not corrupted."
            )
            error_msg += f"\n   File: {self.star_path}"
            error_msg += f"\n   Error: {str(e)}"
            self.result.add_error(error_msg)
    
    def validate_coordinates(self, coords: np.ndarray, 
                           micrograph_shape: Tuple[int, int]) -> list:
        """
        Validate particle coordinates against micrograph dimensions.
        
        Args:
            coords: Array of particle coordinates (N x 2)
            micrograph_shape: Tuple of (height, width)
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        if len(coords) == 0:
            return warnings
        
        height, width = micrograph_shape
        
        # Check for negative coordinates
        negative_mask = (coords[:, 0] < 0) | (coords[:, 1] < 0)
        n_negative = np.sum(negative_mask)
        if n_negative > 0:
            warning_msg = ErrorReporter.get_warning_template(
                'negative_coords',
                n=n_negative
            )
            warnings.append(ErrorReporter.format_warning(warning_msg))
        
        # Check for out-of-bounds coordinates
        out_of_bounds_mask = (coords[:, 0] >= width) | (coords[:, 1] >= height)
        n_out_of_bounds = np.sum(out_of_bounds_mask)
        if n_out_of_bounds > 0:
            warning_msg = ErrorReporter.get_warning_template(
                'out_of_bounds',
                n=n_out_of_bounds,
                w=width,
                h=height
            )
            warnings.append(ErrorReporter.format_warning(warning_msg))
            
            # Check if more than 10% are out of bounds
            percent_out = (n_out_of_bounds / len(coords)) * 100
            if percent_out > 10:
                warning_msg = ErrorReporter.get_warning_template('many_out_of_bounds')
                warnings.append(ErrorReporter.format_warning(warning_msg))
        
        return warnings
