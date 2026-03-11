"""
File Format Detector for CryoEM Interactive Visualization
Detects actual file formats by inspecting content, not just extensions
"""

import os
from dataclasses import dataclass
from typing import Tuple


@dataclass
class FileFormatInfo:
    """Information about detected file format."""
    format_type: str  # 'mrc', 'star', 'text', 'binary', 'unknown'
    confidence: str   # 'high', 'medium', 'low'
    file_size: int
    is_binary: bool
    extension: str
    diagnostic_info: str  # Human-readable description


class FileFormatDetector:
    """Detect file formats by inspecting file content."""
    
    # MRC format magic bytes (MAP signature at bytes 208-211)
    MRC_MAGIC_MAP = b'MAP '
    
    # STAR format keywords
    STAR_KEYWORDS = [b'loop_', b'_rln', b'data_']
    
    @staticmethod
    def detect_format(file_path: str) -> FileFormatInfo:
        """
        Detect file format by inspecting content.
        
        Args:
            file_path: Path to file to inspect
            
        Returns:
            FileFormatInfo with detected format and confidence
        """
        if not os.path.exists(file_path):
            return FileFormatInfo(
                format_type='unknown',
                confidence='low',
                file_size=0,
                is_binary=False,
                extension='',
                diagnostic_info='File does not exist'
            )
        
        file_size = os.path.getsize(file_path)
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Read first 1KB for detection
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)
        except (IOError, OSError) as e:
            return FileFormatInfo(
                format_type='unknown',
                confidence='low',
                file_size=file_size,
                is_binary=False,
                extension=ext,
                diagnostic_info=f'Cannot read file: {str(e)}'
            )
        
        # Check if binary or text
        is_binary = FileFormatDetector._is_binary(header)
        
        # Detect MRC format
        if FileFormatDetector.is_mrc_format(file_path):
            confidence = 'high' if is_binary else 'medium'
            return FileFormatInfo(
                format_type='mrc',
                confidence=confidence,
                file_size=file_size,
                is_binary=is_binary,
                extension=ext,
                diagnostic_info='MRC format detected (binary electron microscopy data)'
            )
        
        # Detect STAR format
        if FileFormatDetector.is_star_format(file_path):
            confidence = 'high' if not is_binary else 'low'
            return FileFormatInfo(
                format_type='star',
                confidence=confidence,
                file_size=file_size,
                is_binary=is_binary,
                extension=ext,
                diagnostic_info='STAR format detected (RELION coordinate file)'
            )
        
        # Generic text or binary
        if is_binary:
            return FileFormatInfo(
                format_type='binary',
                confidence='medium',
                file_size=file_size,
                is_binary=True,
                extension=ext,
                diagnostic_info='Binary file (not MRC format)'
            )
        else:
            return FileFormatInfo(
                format_type='text',
                confidence='medium',
                file_size=file_size,
                is_binary=False,
                extension=ext,
                diagnostic_info='Text file (not STAR format)'
            )
    
    @staticmethod
    def is_mrc_format(file_path: str) -> bool:
        """
        Check if file appears to be MRC format.
        
        MRC files have MAP signature at bytes 208-211 or are binary with .mrc/.mrcs/.st extension.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            True if file appears to be MRC format
        """
        try:
            with open(file_path, 'rb') as f:
                # Check for MAP signature at bytes 208-211
                f.seek(208)
                signature = f.read(4)
                if signature == FileFormatDetector.MRC_MAGIC_MAP:
                    return True
                
                # Alternative: check if binary with MRC extension
                _, ext = os.path.splitext(file_path)
                ext = ext.lower()
                if ext in ['.mrc', '.mrcs', '.st']:
                    # Read first 1KB to check if binary
                    f.seek(0)
                    header = f.read(1024)
                    if FileFormatDetector._is_binary(header):
                        return True
            
            return False
        except (IOError, OSError):
            return False
    
    @staticmethod
    def is_star_format(file_path: str) -> bool:
        """
        Check if file appears to be STAR format.
        
        STAR files contain keywords like 'loop_', '_rln', or 'data_'.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            True if file appears to be STAR format
        """
        try:
            with open(file_path, 'rb') as f:
                # Read first 1KB
                content = f.read(1024)
                
                # Check for STAR keywords
                for keyword in FileFormatDetector.STAR_KEYWORDS:
                    if keyword in content:
                        return True
                
                # Check if text file with .star extension
                _, ext = os.path.splitext(file_path)
                ext = ext.lower()
                if ext in ['.star', '.txt']:
                    # Verify it's text (not binary)
                    if not FileFormatDetector._is_binary(content):
                        # Check for typical STAR structure (columns with underscores)
                        if b'_' in content:
                            return True
            
            return False
        except (IOError, OSError):
            return False
    
    @staticmethod
    def _is_binary(data: bytes) -> bool:
        """
        Check if data appears to be binary (not text).
        
        Args:
            data: Bytes to check
            
        Returns:
            True if data appears to be binary
        """
        # Check for null bytes (common in binary files)
        if b'\x00' in data:
            return True
        
        # Check for high proportion of non-ASCII bytes
        try:
            data.decode('ascii')
            return False  # Successfully decoded as ASCII, likely text
        except UnicodeDecodeError:
            # Try UTF-8
            try:
                data.decode('utf-8')
                return False  # Successfully decoded as UTF-8, likely text
            except UnicodeDecodeError:
                return True  # Cannot decode, likely binary
