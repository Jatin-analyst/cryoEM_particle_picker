"""
Error Reporter for CryoEM Interactive Visualization
Formats and displays error messages with consistent styling
"""

import sys
from typing import Optional
from .validation_result import ValidationResult


# Error message templates with descriptions and suggestions
ERROR_TEMPLATES = {
    'duplicate_files': (
        "The same file was selected for both micrograph and STAR file inputs.",
        "Please select different files: one MRC/MRCS/ST micrograph and one STAR coordinate file."
    ),
    'galaxy_duplicate_dataset': (
        "Galaxy passed the same dataset for both inputs. This may indicate a workflow configuration issue.",
        "Please verify your workflow connections and ensure the micrograph input receives the original image file, not the STAR coordinates."
    ),
    'wrong_format_micrograph': (
        "The micrograph file appears to be a {detected} file, not an MRC format.",
        "Please provide an MRC/MRCS/ST format micrograph file. You may have selected the wrong output from the particle picker tool."
    ),
    'wrong_format_star': (
        "The STAR file appears to be a {detected} file, not a STAR format.",
        "Please provide a STAR format coordinate file (text file with loop_ structure)."
    ),
    'empty_micrograph': (
        "The micrograph file is empty or corrupted.",
        "Please verify the file integrity and try re-exporting from your picking software."
    ),
    'empty_star': (
        "The STAR file is empty (0 bytes).",
        "Please provide a valid STAR file with particle coordinates."
    ),
    'no_data_loop': (
        "The STAR file does not contain a valid data loop.",
        "Expected format: 'loop_' followed by column definitions (_rlnCoordinateX, etc.) and data rows."
    ),
    'no_particles': (
        "No valid particles found in STAR file.",
        "The file may be from a failed picking run or have incorrect formatting."
    ),
    'invalid_star_columns': (
        "Invalid STAR file format: data rows must contain at least 3 columns (X, Y, confidence). Found {n} columns.",
        "Please check the STAR file was generated correctly by the particle picker."
    ),
}

# Warning message templates
WARNING_TEMPLATES = {
    'negative_coords': "Found {n} particles with negative coordinates. These may indicate data quality issues.",
    'out_of_bounds': "Found {n} particles outside micrograph boundaries (width: {w}, height: {h}). These particles will not be visible.",
    'many_out_of_bounds': "More than 10% of particles are outside micrograph boundaries. This suggests a coordinate system mismatch.",
}


class ErrorReporter:
    """Format and display error messages with consistent styling."""
    
    @staticmethod
    def format_error(message: str, suggestion: Optional[str] = None) -> str:
        """
        Format an error message with icon and suggestion.
        
        Args:
            message: The error description
            suggestion: Optional actionable suggestion
            
        Returns:
            Formatted error string
        """
        formatted = f"❌ ERROR: {message}"
        if suggestion:
            formatted += f"\n   💡 {suggestion}"
        return formatted
    
    @staticmethod
    def format_warning(message: str) -> str:
        """
        Format a warning message with icon.
        
        Args:
            message: The warning description
            
        Returns:
            Formatted warning string
        """
        return f"⚠️  WARNING: {message}"
    
    @staticmethod
    def report_validation_results(result: ValidationResult):
        """
        Print all errors and warnings from validation.
        
        Args:
            result: ValidationResult containing errors and warnings
        """
        if result.has_errors():
            print("\n" + "="*60, file=sys.stderr)
            print("VALIDATION ERRORS", file=sys.stderr)
            print("="*60, file=sys.stderr)
            for i, error in enumerate(result.errors, 1):
                print(f"\n{i}. {error}", file=sys.stderr)
            print("\n" + "="*60 + "\n", file=sys.stderr)
        
        if result.has_warnings():
            print("\n" + "-"*60, file=sys.stderr)
            print("VALIDATION WARNINGS", file=sys.stderr)
            print("-"*60, file=sys.stderr)
            for i, warning in enumerate(result.warnings, 1):
                print(f"\n{i}. {warning}", file=sys.stderr)
            print("\n" + "-"*60 + "\n", file=sys.stderr)
    
    @staticmethod
    def format_file_info(file_path: str, detected_format: str, 
                        expected_format: str) -> str:
        """
        Format diagnostic information about file format mismatch.
        
        Args:
            file_path: Path to the file
            detected_format: Format that was detected
            expected_format: Format that was expected
            
        Returns:
            Formatted diagnostic string
        """
        return (
            f"File: {file_path}\n"
            f"   Expected: {expected_format}\n"
            f"   Detected: {detected_format}"
        )
    
    @staticmethod
    def get_error_template(template_key: str, **kwargs) -> tuple:
        """
        Get error message template with formatting.
        
        Args:
            template_key: Key for error template
            **kwargs: Format arguments for template
            
        Returns:
            Tuple of (formatted_message, suggestion)
        """
        if template_key not in ERROR_TEMPLATES:
            return (f"Unknown error: {template_key}", None)
        
        message, suggestion = ERROR_TEMPLATES[template_key]
        
        # Format message with provided arguments
        try:
            message = message.format(**kwargs)
        except KeyError:
            pass  # Use unformatted message if keys don't match
        
        return (message, suggestion)
    
    @staticmethod
    def get_warning_template(template_key: str, **kwargs) -> str:
        """
        Get warning message template with formatting.
        
        Args:
            template_key: Key for warning template
            **kwargs: Format arguments for template
            
        Returns:
            Formatted warning message
        """
        if template_key not in WARNING_TEMPLATES:
            return f"Unknown warning: {template_key}"
        
        message = WARNING_TEMPLATES[template_key]
        
        # Format message with provided arguments
        try:
            message = message.format(**kwargs)
        except KeyError:
            pass  # Use unformatted message if keys don't match
        
        return message
