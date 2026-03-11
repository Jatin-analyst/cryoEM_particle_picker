"""
Validation Result data model for CryoEM Interactive Visualization
Container for validation errors and warnings
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ValidationResult:
    """Container for validation results."""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    is_valid: bool = True
    
    def add_error(self, message: str):
        """
        Add a critical error.
        
        Args:
            message: Error message to add
        """
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """
        Add a non-critical warning.
        
        Args:
            message: Warning message to add
        """
        self.warnings.append(message)
    
    def has_errors(self) -> bool:
        """
        Check if there are any errors.
        
        Returns:
            True if errors exist
        """
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """
        Check if there are any warnings.
        
        Returns:
            True if warnings exist
        """
        return len(self.warnings) > 0
    
    def get_error_count(self) -> int:
        """
        Get the number of errors.
        
        Returns:
            Number of errors
        """
        return len(self.errors)
    
    def get_warning_count(self) -> int:
        """
        Get the number of warnings.
        
        Returns:
            Number of warnings
        """
        return len(self.warnings)
