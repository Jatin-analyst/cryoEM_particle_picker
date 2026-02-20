#!/usr/bin/env python3
"""
Batch processing CLI for CryoEM particle picker
Processes multiple micrographs from a directory
"""

import argparse
import sys
from pathlib import Path

# Import from lib
try:
    from lib.batch_processing import BatchProcessor
    from lib import setup_logging, get_logger, ExitCode, handle_error, FileIOError
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'lib'))
    from batch_processing import BatchProcessor
    from error_handling import ExitCode, handle_error, FileIOError
    from logging_config import setup_logging, get_logger


def parse_arguments():
    """Parse command line arguments for batch processing"""
    parser = argparse.ArgumentParser(
        description='Batch particle picking for multiple CryoEM micrographs',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument(
        '--input_dir',
        type=str,
        required=True,
        help='Input directory containing micrographs (.mrc, .mrcs, .st files)'
    )
    
    parser.add_argument(
        '--output_dir',
        type=str,
        required=True,
        help='Output directory for STAR files'
    )
    
    parser.add_argument(
        '--particle_size',
        type=int,
        required=True,
        help='Particle diameter in pixels (50-1000)'
    )
    
    # Model parameters
    parser.add_argument(
        '--model_path',
        type=str,
        default=None,
        help='Path to custom model weights (default: use pretrained)'
    )
    
    parser.add_argument(
        '--confidence_threshold',
        type=float,
        default=0.7,
        help='Confidence threshold for particle detection (0.1-0.99)'
    )
    
    # Performance options
    parser.add_argument(
        '--device',
        type=str,
        choices=['cpu', 'cuda'],
        default='cpu',
        help='Device for inference'
    )
    
    parser.add_argument(
        '--batch_size',
        type=int,
        default=128,
        help='Batch size for inference'
    )
    
    # Batch processing options
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Search subdirectories recursively'
    )
    
    parser.add_argument(
        '--preserve_structure',
        action='store_true',
        help='Preserve directory structure in output'
    )
    
    parser.add_argument(
        '--max_files',
        type=int,
        default=None,
        help='Maximum number of files to process (for testing)'
    )
    
    # Post-processing options
    parser.add_argument(
        '--min_distance',
        type=int,
        default=None,
        help='Minimum distance between particles (default: particle_size)'
    )
    
    parser.add_argument(
        '--edge_exclusion',
        type=int,
        default=0,
        help='Exclude particles within N pixels of edge'
    )
    
    # CTF estimation
    parser.add_argument(
        '--ctf_estimation',
        action='store_true',
        help='Enable CTF parameter estimation'
    )
    
    parser.add_argument(
        '--voltage',
        type=float,
        default=300.0,
        help='Acceleration voltage (kV) for CTF estimation'
    )
    
    parser.add_argument(
        '--cs',
        type=float,
        default=2.7,
        help='Spherical aberration (mm) for CTF estimation'
    )
    
    parser.add_argument(
        '--pixel_size',
        type=float,
        default=1.0,
        help='Pixel size (Angstroms/pixel) for CTF estimation'
    )
    
    # Output options
    parser.add_argument(
        '--summary_report',
        type=str,
        default=None,
        help='Path for JSON summary report'
    )
    
    # Verbosity
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed progress information'
    )
    
    parser.add_argument(
        '--log_file',
        type=str,
        default=None,
        help='Optional log file path'
    )
    
    return parser.parse_args()


def process_single_file(input_path: str, output_path: str, **kwargs):
    """
    Process a single micrograph file
    This is a wrapper that calls the main ml_picker logic
    
    Args:
        input_path: Path to input micrograph
        output_path: Path for output STAR file
        **kwargs: Additional processing parameters
        
    Returns:
        Dict with processing results
    """
    # Import the main processing function
    try:
        from lib.preprocessing import load_micrograph_mmap, normalize_micrograph
        from lib.ml_model.picker import load_model_cached, get_default_model_path
        from lib.ml_model.Inference import FastInferenceEngine
        from lib.postprocessing import filter_by_confidence, non_maximum_suppression, apply_edge_exclusion
        from lib.ctf import CTFEstimator
        from lib.utils import write_star_file
    except ImportError:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'lib'))
        from preprocessing import load_micrograph_mmap, normalize_micrograph
        from ml_model.picker import load_model_cached, get_default_model_path
        from ml_model.Inference import FastInferenceEngine
        from postprocessing import filter_by_confidence, non_maximum_suppression, apply_edge_exclusion
        from ctf import CTFEstimator
        from utils import write_star_file
    
    # Extract parameters
    particle_size = kwargs['particle_size']
    confidence_threshold = kwargs['confidence_threshold']
    device = kwargs['device']
    batch_size = kwargs.get('batch_size', 128)
    min_distance = kwargs.get('min_distance', particle_size)
    edge_exclusion = kwargs.get('edge_exclusion', 0)
    ctf_estimation = kwargs.get('ctf_estimation', False)
    model_path = kwargs.get('model_path')
    
    # Load micrograph
    micrograph = load_micrograph_mmap(input_path)
    
    # Normalize
    micrograph_norm = normalize_micrograph(micrograph)
    
    # Load model (use cached if available)
    if model_path is None:
        model_path = get_default_model_path()
    
    model = load_model_cached(model_path, device=device)
    
    # Initialize inference engine
    engine = FastInferenceEngine(
        model,
        device=device,
        use_amp=(device == 'cuda')
    )
    engine.batch_size = batch_size
    
    # Run inference
    coords, confidences = engine.predict_micrograph(
        micrograph_norm,
        particle_size=particle_size,
        conf_threshold=confidence_threshold * 0.5
    )
    
    # Post-processing
    coords, confidences = filter_by_confidence(coords, confidences, confidence_threshold)
    coords, confidences = non_maximum_suppression(coords, confidences, min_distance)
    
    if edge_exclusion > 0:
        coords, confidences = apply_edge_exclusion(
            coords, confidences, micrograph.shape, edge_exclusion
        )
    
    # CTF estimation (if requested)
    ctf_params = None
    if ctf_estimation:
        try:
            ctf_estimator = CTFEstimator(
                voltage=kwargs.get('voltage', 300.0),
                cs=kwargs.get('cs', 2.7),
                pixel_size=kwargs.get('pixel_size', 1.0)
            )
            ctf_params = ctf_estimator.estimate(micrograph)
        except Exception as e:
            # CTF estimation is non-fatal
            logger = get_logger(__name__)
            logger.warning(f"CTF estimation failed: {e}")
    
    # Write output
    write_star_file(
        output_path,
        coords,
        confidences,
        ctf_params=ctf_params,
        micrograph_name=Path(input_path).name
    )
    
    return {
        'particles_detected': len(coords),
        'mean_confidence': float(confidences.mean()) if len(confidences) > 0 else 0.0
    }


def main():
    """Main execution function for batch processing"""
    args = parse_arguments()
    
    # Set up logging
    logger = setup_logging(verbose=args.verbose, log_file=args.log_file)
    
    try:
        logger.info("="*60)
        logger.info("CryoEM Particle Picker - Batch Processing Mode")
        logger.info("="*60)
        logger.info(f"Input directory: {args.input_dir}")
        logger.info(f"Output directory: {args.output_dir}")
        logger.info(f"Particle size: {args.particle_size} pixels")
        logger.info(f"Confidence threshold: {args.confidence_threshold}")
        logger.info(f"Device: {args.device}")
        logger.info(f"Recursive search: {args.recursive}")
        logger.info("="*60)
        
        # Initialize batch processor
        batch_processor = BatchProcessor(
            output_dir=Path(args.output_dir),
            create_subdirs=args.preserve_structure
        )
        
        # Prepare processing parameters
        process_kwargs = {
            'particle_size': args.particle_size,
            'confidence_threshold': args.confidence_threshold,
            'device': args.device,
            'batch_size': args.batch_size,
            'min_distance': args.min_distance,
            'edge_exclusion': args.edge_exclusion,
            'ctf_estimation': args.ctf_estimation,
            'voltage': args.voltage,
            'cs': args.cs,
            'pixel_size': args.pixel_size,
            'model_path': args.model_path
        }
        
        # Process batch
        summary = batch_processor.process_batch(
            input_dir=Path(args.input_dir),
            process_func=process_single_file,
            recursive=args.recursive,
            max_files=args.max_files,
            **process_kwargs
        )
        
        # Save summary report if requested
        if args.summary_report:
            batch_processor.save_summary_report(Path(args.summary_report))
        
        # Exit with appropriate code
        if summary.failed > 0:
            logger.warning(f"{summary.failed} files failed to process")
            return ExitCode.PROCESSING_ERROR if summary.successful == 0 else ExitCode.SUCCESS
        
        return ExitCode.SUCCESS
        
    except FileIOError as e:
        handle_error(e, ExitCode.FILE_IO_ERROR)
    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"ERROR: Unexpected error - {str(e)}", file=sys.stderr)
        return ExitCode.PROCESSING_ERROR


if __name__ == '__main__':
    sys.exit(main())
