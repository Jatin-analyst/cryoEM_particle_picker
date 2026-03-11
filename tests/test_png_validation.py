#!/usr/bin/env python3
"""
PNG Validation Test Utilities
Tests for Galaxy PNG display fix
"""

import os
from pathlib import Path


def validate_png_magic_bytes(file_path: str) -> bool:
    """
    Validate that a file has correct PNG magic bytes.
    
    PNG files start with 8 bytes: 89 50 4E 47 0D 0A 1A 0A
    (0x89, 'P', 'N', 'G', '\r', '\n', 0x1A, '\n')
    
    Args:
        file_path: Path to file to check
        
    Returns:
        True if file has valid PNG magic bytes, False otherwise
    """
    PNG_MAGIC_BYTES = b'\x89PNG\r\n\x1a\n'
    
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
            return header == PNG_MAGIC_BYTES
    except (IOError, OSError):
        return False


def validate_png_openable(file_path: str) -> bool:
    """
    Validate that a PNG file can be opened by PIL/Pillow.
    
    Args:
        file_path: Path to PNG file to check
        
    Returns:
        True if file can be opened successfully, False otherwise
    """
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            # Verify it's actually a PNG
            return img.format == 'PNG'
    except Exception:
        return False


if __name__ == '__main__':
    # Simple test
    import tempfile
    import matplotlib.pyplot as plt
    
    # Create a test PNG
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Generate a simple plot
        plt.figure(figsize=(4, 3))
        plt.plot([1, 2, 3], [1, 4, 9])
        plt.title('Test Plot')
        plt.savefig(tmp_path)
        plt.close()
        
        # Test validation functions
        print(f"Testing PNG validation with: {tmp_path}")
        print(f"Magic bytes valid: {validate_png_magic_bytes(tmp_path)}")
        print(f"PIL can open: {validate_png_openable(tmp_path)}")
        
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
