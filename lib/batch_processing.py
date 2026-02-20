"""
Batch processing module for handling multiple micrographs
Supports directory-based processing with error handling and summary reports
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json

from .logging_config import get_logger
from .error_handling import FileIOError, ProcessingError

logger = get_logger(__name__)


@dataclass
class BatchResult:
    """Result of processing a single file in batch mode"""
    filename: str
    success: bool
    particles_detected: int
    processing_time: float
    error_message: Optional[str] = None


@dataclass
class BatchSummary:
    """Summary of batch processing results"""
    total_files: int
    successful: int
    failed: int
    total_particles: int
    total_time: float
    results: List[BatchResult]
    
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_files == 0:
            return 0.0
        return (self.successful / self.total_files) * 100.0
    
    def average_particles_per_file(self) -> float:
        """Calculate average particles per successful file"""
        if self.successful == 0:
            return 0.0
        return self.total_particles / self.successful
    
    def average_time_per_file(self) -> float:
        """Calculate average processing time per file"""
        if self.total_files == 0:
            return 0.0
        return self.total_time / self.total_files


class BatchProcessor:
    """
    Handles batch processing of multiple micrographs
    
    Features:
    - Directory-based input
    - Per-file error handling (failures don't stop batch)
    - Progress reporting
    - Summary statistics
    - JSON report generation
    """
    
    SUPPORTED_EXTENSIONS = {'.mrc', '.mrcs', '.st'}
    
    def __init__(self, output_dir: Path, create_subdirs: bool = False):
        """
        Initialize batch processor
        
        Args:
            output_dir: Directory for output STAR files
            create_subdirs: If True, create subdirectories matching input structure
        """
        self.output_dir = Path(output_dir)
        self.create_subdirs = create_subdirs
        self.results: List[BatchResult] = []
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Batch processor initialized with output directory: {self.output_dir}")
    
    def find_micrographs(self, input_dir: Path, recursive: bool = True) -> List[Path]:
        """
        Find all supported micrograph files in directory
        
        Args:
            input_dir: Directory to search
            recursive: If True, search subdirectories recursively
            
        Returns:
            List of paths to micrograph files
            
        Raises:
            FileIOError: If input directory doesn't exist or is not accessible
        """
        input_path = Path(input_dir)
        
        if not input_path.exists():
            raise FileIOError(f"Input directory does not exist: {input_dir}")
        
        if not input_path.is_dir():
            raise FileIOError(f"Input path is not a directory: {input_dir}")
        
        micrographs = []
        
        if recursive:
            # Search recursively
            for ext in self.SUPPORTED_EXTENSIONS:
                micrographs.extend(input_path.rglob(f"*{ext}"))
        else:
            # Search only top level
            for ext in self.SUPPORTED_EXTENSIONS:
                micrographs.extend(input_path.glob(f"*{ext}"))
        
        # Sort for consistent ordering
        micrographs.sort()
        
        logger.info(f"Found {len(micrographs)} micrograph files in {input_dir}")
        
        return micrographs
    
    def get_output_path(self, input_path: Path, input_base_dir: Path) -> Path:
        """
        Determine output path for a given input file
        
        Args:
            input_path: Path to input micrograph
            input_base_dir: Base directory for input files
            
        Returns:
            Path for output STAR file
        """
        # Generate output filename
        output_filename = input_path.stem + "_particles.star"
        
        if self.create_subdirs:
            # Preserve directory structure
            try:
                relative_dir = input_path.parent.relative_to(input_base_dir)
                output_subdir = self.output_dir / relative_dir
                output_subdir.mkdir(parents=True, exist_ok=True)
                return output_subdir / output_filename
            except ValueError:
                # If relative path fails, use flat structure
                return self.output_dir / output_filename
        else:
            # Flat structure - all outputs in same directory
            return self.output_dir / output_filename
    
    def process_file(
        self,
        input_path: Path,
        output_path: Path,
        process_func,
        **kwargs
    ) -> BatchResult:
        """
        Process a single micrograph file
        
        Args:
            input_path: Path to input micrograph
            output_path: Path for output STAR file
            process_func: Function to call for processing (should accept input, output, **kwargs)
            **kwargs: Additional arguments to pass to process_func
            
        Returns:
            BatchResult with processing outcome
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing: {input_path.name}")
            
            # Call the processing function
            result = process_func(
                input_path=str(input_path),
                output_path=str(output_path),
                **kwargs
            )
            
            # Extract number of particles from result
            particles_detected = result.get('particles_detected', 0) if isinstance(result, dict) else 0
            
            elapsed = time.time() - start_time
            
            logger.info(f"  ✓ Success: {particles_detected} particles in {elapsed:.2f}s")
            
            return BatchResult(
                filename=input_path.name,
                success=True,
                particles_detected=particles_detected,
                processing_time=elapsed
            )
            
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"  ✗ Failed: {error_msg}")
            
            return BatchResult(
                filename=input_path.name,
                success=False,
                particles_detected=0,
                processing_time=elapsed,
                error_message=error_msg
            )
    
    def process_batch(
        self,
        input_dir: Path,
        process_func,
        recursive: bool = True,
        max_files: Optional[int] = None,
        **kwargs
    ) -> BatchSummary:
        """
        Process all micrographs in a directory
        
        Args:
            input_dir: Directory containing micrographs
            process_func: Function to call for each file
            recursive: If True, search subdirectories
            max_files: Maximum number of files to process (None = all)
            **kwargs: Additional arguments to pass to process_func
            
        Returns:
            BatchSummary with overall results
        """
        batch_start = time.time()
        
        # Find all micrographs
        micrographs = self.find_micrographs(input_dir, recursive=recursive)
        
        if len(micrographs) == 0:
            logger.warning(f"No micrograph files found in {input_dir}")
            return BatchSummary(
                total_files=0,
                successful=0,
                failed=0,
                total_particles=0,
                total_time=0.0,
                results=[]
            )
        
        # Limit number of files if requested
        if max_files is not None and max_files > 0:
            micrographs = micrographs[:max_files]
            logger.info(f"Processing limited to first {max_files} files")
        
        logger.info(f"Starting batch processing of {len(micrographs)} files")
        logger.info("=" * 60)
        
        # Process each file
        self.results = []
        for i, input_path in enumerate(micrographs, 1):
            logger.info(f"[{i}/{len(micrographs)}] {input_path.name}")
            
            output_path = self.get_output_path(input_path, input_dir)
            
            result = self.process_file(
                input_path=input_path,
                output_path=output_path,
                process_func=process_func,
                **kwargs
            )
            
            self.results.append(result)
        
        batch_elapsed = time.time() - batch_start
        
        # Generate summary
        summary = self._generate_summary(batch_elapsed)
        
        logger.info("=" * 60)
        logger.info("Batch Processing Complete!")
        logger.info(f"Total files: {summary.total_files}")
        logger.info(f"Successful: {summary.successful}")
        logger.info(f"Failed: {summary.failed}")
        logger.info(f"Success rate: {summary.success_rate():.1f}%")
        logger.info(f"Total particles: {summary.total_particles}")
        logger.info(f"Average particles/file: {summary.average_particles_per_file():.1f}")
        logger.info(f"Total time: {summary.total_time:.2f}s")
        logger.info(f"Average time/file: {summary.average_time_per_file():.2f}s")
        logger.info("=" * 60)
        
        return summary
    
    def _generate_summary(self, total_time: float) -> BatchSummary:
        """Generate summary from results"""
        successful = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results if not r.success)
        total_particles = sum(r.particles_detected for r in self.results)
        
        return BatchSummary(
            total_files=len(self.results),
            successful=successful,
            failed=failed,
            total_particles=total_particles,
            total_time=total_time,
            results=self.results
        )
    
    def save_summary_report(self, output_path: Path):
        """
        Save batch processing summary to JSON file
        
        Args:
            output_path: Path for JSON report file
        """
        if not self.results:
            logger.warning("No results to save")
            return
        
        summary = self._generate_summary(
            sum(r.processing_time for r in self.results)
        )
        
        report = {
            'summary': {
                'total_files': summary.total_files,
                'successful': summary.successful,
                'failed': summary.failed,
                'success_rate': summary.success_rate(),
                'total_particles': summary.total_particles,
                'average_particles_per_file': summary.average_particles_per_file(),
                'total_time': summary.total_time,
                'average_time_per_file': summary.average_time_per_file()
            },
            'results': [
                {
                    'filename': r.filename,
                    'success': r.success,
                    'particles_detected': r.particles_detected,
                    'processing_time': r.processing_time,
                    'error_message': r.error_message
                }
                for r in self.results
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Summary report saved to: {output_path}")
