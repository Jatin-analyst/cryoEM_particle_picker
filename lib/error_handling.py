"""
Error handling framework for CryoEM Precision Tool
Defines error categories, exit codes, and error message formatting
"""

import sys
from enum import IntEnum
from typing import Optional


class ExitCode(IntEnum):
    """Exit codes for different error categories."""
    SUCCESS = 0
    INPUT_VALIDATION_ERROR = 1
    FILE_IO_ERROR = 2
    MODEL_ERROR = 3
    PROCESSING_ERROR = 4


class CryoEMError(Exception):
    """Base exception for CryoEM Precision Tool errors."""
    
    def __init__(self, category: str, issue: str, details: str, suggestion: str):
        self.category = category
        self.issue = issue
        self.details = details
        self.suggestion = suggestion
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        """Format error message according to standard format."""
        return (
            f"ERROR: {self.category} - {self.issue}\n"
            f"Details: {self.details}\n"
            f"Suggestion: {self.suggestion}"
        )


class InputValidationError(CryoEMError):
    """Error for invalid input parameters or files."""
    
    def __init__(self, issue: str, details: str, suggestion: str):
        super().__init__("Input Validation", issue, details, suggestion)


class FileIOError(CryoEMError):
    """Error for file reading/writing issues."""
    
    def __init__(self, issue: str, details: str, suggestion: str):
        super().__init__("File I/O", issue, details, suggestion)


class ModelError(CryoEMError):
    """Error for model loading or inference issues."""
    
    def __init__(self, issue: str, details: str, suggestion: str):
        super().__init__("Model", issue, details, suggestion)


class ProcessingError(CryoEMError):
    """Error for processing failures."""
    
    def __init__(self, issue: str, details: str, suggestion: str):
        super().__init__("Processing", issue, details, suggestion)


def handle_error(error: Exception, exit_code: ExitCode) -> None:
    """
    Handle error by printing message and exiting with appropriate code.
    
    Args:
        error: Exception to handle
        exit_code: Exit code to use
    """
    print(str(error), file=sys.stderr)
    sys.exit(exit_code)


def validate_particle_size(particle_size: int) -> None:
    """
    Validate particle size parameter.
    
    Args:
        particle_size: Particle diameter in pixels
        
    Raises:
        InputValidationError: If particle size is out of valid range
    """
    if not 50 <= particle_size <= 1000:
        raise InputValidationError(
            issue="Invalid particle diameter",
            details=f"Particle diameter must be between 50 and 1000 pixels, got {particle_size}",
            suggestion="Adjust the particle_size parameter to be within the valid range"
        )


def validate_confidence_threshold(threshold: float) -> None:
    """
    Validate confidence threshold parameter.
    
    Args:
        threshold: Confidence threshold value
        
    Raises:
        InputValidationError: If threshold is out of valid range
    """
    if not 0.1 <= threshold <= 0.99:
        raise InputValidationError(
            issue="Invalid confidence threshold",
            details=f"Confidence threshold must be between 0.1 and 0.99, got {threshold}",
            suggestion="Adjust the confidence_threshold parameter to be within the valid range"
        )


def validate_file_exists(filepath: str, file_description: str = "File") -> None:
    """
    Validate that a file exists.
    
    Args:
        filepath: Path to file
        file_description: Description of file for error message
        
    Raises:
        FileIOError: If file does not exist
    """
    from pathlib import Path
    
    if not Path(filepath).exists():
        raise FileIOError(
            issue=f"{file_description} not found",
            details=f"Cannot find file: {filepath}",
            suggestion=f"Check that the file path is correct and the file exists"
        )
