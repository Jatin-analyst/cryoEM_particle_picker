"""
Storage integration module
Handles external storage mounts (NFS, Lustre, BeeGFS)
"""

from .external_mounts import StorageManager

__all__ = ['StorageManager']
