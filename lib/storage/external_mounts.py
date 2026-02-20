"""
Storage integration module
Handles external storage mounts (NFS, Lustre, BeeGFS)
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

from ..error_handling import FileIOError
from ..logging_config import get_logger

logger = get_logger(__name__)


class StorageManager:
    """
    Manage external storage mounts.
    
    Supports:
    - NFS (Network File System)
    - Lustre (parallel distributed filesystem)
    - BeeGFS (parallel cluster filesystem)
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize storage manager.
        
        Args:
            config_path: Path to storage configuration YAML file
        """
        self.mount_points: List[Dict[str, str]] = []
        
        if config_path and Path(config_path).exists():
            self._load_config(config_path)
        else:
            logger.info("No storage configuration provided, using local filesystem only")
    
    def _load_config(self, config_path: str) -> None:
        """
        Load storage configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if 'mount_points' in config:
                self.mount_points = config['mount_points']
                logger.info(f"Loaded {len(self.mount_points)} storage mount points")
                
                # Validate each mount
                for mount in self.mount_points:
                    mount_type = mount.get('type', 'unknown')
                    mount_path = mount.get('path', '')
                    
                    if self.validate_mount(mount_type, mount_path):
                        logger.info(f"  ✓ {mount_type}: {mount_path}")
                    else:
                        logger.warning(f"  ✗ {mount_type}: {mount_path} (not accessible)")
            
        except Exception as e:
            logger.warning(f"Failed to load storage config: {e}")
    
    def resolve_path(self, filepath: str) -> str:
        """
        Resolve file path, checking external mounts.
        
        Args:
            filepath: Input file path (can be relative or absolute)
            
        Returns:
            Resolved absolute path
            
        Raises:
            FileIOError: If file cannot be found on any mount
        """
        filepath_obj = Path(filepath)
        
        # If path is absolute and exists, return it
        if filepath_obj.is_absolute() and filepath_obj.exists():
            return str(filepath_obj.resolve())
        
        # If path is relative and exists locally, return it
        if filepath_obj.exists():
            return str(filepath_obj.resolve())
        
        # Check each configured mount point
        for mount in self.mount_points:
            mount_path = Path(mount.get('path', ''))
            
            # Try joining with mount path
            candidate = mount_path / filepath
            if candidate.exists():
                logger.info(f"Found file on {mount.get('type')} mount: {candidate}")
                return str(candidate.resolve())
            
            # Try treating filepath as relative to mount
            if filepath_obj.is_absolute():
                # Strip leading slash and try again
                relative = str(filepath_obj).lstrip('/')
                candidate = mount_path / relative
                if candidate.exists():
                    logger.info(f"Found file on {mount.get('type')} mount: {candidate}")
                    return str(candidate.resolve())
        
        # File not found anywhere
        raise FileIOError(
            issue="File not found",
            details=f"Cannot find file {filepath} on local filesystem or any configured storage mount",
            suggestion="Check that the file path is correct and storage mounts are accessible"
        )
    
    def validate_mount(self, mount_type: str, mount_path: str) -> bool:
        """
        Validate that a storage mount is accessible.
        
        Args:
            mount_type: Type of mount (nfs/lustre/beegfs)
            mount_path: Mount point path
            
        Returns:
            True if mount is accessible, False otherwise
        """
        mount_path_obj = Path(mount_path)
        
        # Check if path exists
        if not mount_path_obj.exists():
            return False
        
        # Check if path is a directory
        if not mount_path_obj.is_dir():
            return False
        
        # Check if we can read the directory
        try:
            list(mount_path_obj.iterdir())
            return True
        except PermissionError:
            return False
        except Exception:
            return False
    
    def optimize_io_for_filesystem(self, mount_type: str) -> Dict[str, Any]:
        """
        Get optimized I/O parameters for filesystem type.
        
        Different filesystems have different optimal I/O patterns:
        - NFS: Larger buffer sizes, fewer small operations
        - Lustre: Stripe-aligned I/O, parallel access
        - BeeGFS: Optimized for parallel workloads
        
        Args:
            mount_type: Type of filesystem (nfs/lustre/beegfs/local)
            
        Returns:
            Dictionary with buffer sizes, read-ahead settings, etc.
        """
        if mount_type.lower() == 'nfs':
            return {
                'buffer_size': 1024 * 1024,  # 1 MB
                'read_ahead': True,
                'cache_enabled': True,
                'parallel_io': False,
                'stripe_size': None
            }
        
        elif mount_type.lower() == 'lustre':
            return {
                'buffer_size': 4 * 1024 * 1024,  # 4 MB
                'read_ahead': True,
                'cache_enabled': True,
                'parallel_io': True,
                'stripe_size': 1024 * 1024  # 1 MB stripe
            }
        
        elif mount_type.lower() == 'beegfs':
            return {
                'buffer_size': 2 * 1024 * 1024,  # 2 MB
                'read_ahead': True,
                'cache_enabled': True,
                'parallel_io': True,
                'stripe_size': 512 * 1024  # 512 KB stripe
            }
        
        else:  # local or unknown
            return {
                'buffer_size': 512 * 1024,  # 512 KB
                'read_ahead': False,
                'cache_enabled': True,
                'parallel_io': False,
                'stripe_size': None
            }
    
    def get_filesystem_type(self, filepath: str) -> str:
        """
        Determine filesystem type for a given file path.
        
        Args:
            filepath: File path to check
            
        Returns:
            Filesystem type ('nfs', 'lustre', 'beegfs', or 'local')
        """
        filepath_obj = Path(filepath).resolve()
        
        # Check each mount point
        for mount in self.mount_points:
            mount_path = Path(mount.get('path', '')).resolve()
            
            # Check if filepath is under this mount
            try:
                filepath_obj.relative_to(mount_path)
                return mount.get('type', 'local').lower()
            except ValueError:
                continue
        
        # Not on any configured mount
        return 'local'
