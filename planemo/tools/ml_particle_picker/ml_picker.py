#!/usr/bin/env python3
"""
ML-based particle picker for CryoEM micrographs
Optimized for speed and precision with CTF estimation
"""

import argparse
import sys
import time
import numpy as np
from pathlib import Path

# Import from lib (Galaxy will set PYTHONPATH or use relative imports)
try:
    # Try absolute imports first (when installed as package)
    from lib.preprocessing import load_micrograph_mmap, normalize_micrograph
    from lib.ml_model.picker import load_model_cached
    from lib.ml_model.Inference import FastInferenceEngine
    from lib.postprocessing import filter_by_confidence, non_maximum_suppression, apply_edge_exclusion
    from lib.ctf import CTFEstimator
    from lib.utils import write_star_file, write_confidence_map, generate_statistics_plot
    from lib.storage import StorageManager
    from lib import (
        setup_logging, get_logger,
        ExitCode, handle_error,
        validate_particle_size, validate_confidence_threshold,
        InputValidationError, FileIOError, ModelError, ProcessingError
    )
except ImportError:
    # Fallback to relative imports (when running from source)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'lib'))
    
    from preprocessing import load_micrograph_mmap, normalize_micrograph
    from ml_model.picker import load_model_cached
    from ml_model.Inference import FastInferenceEngine
    from postprocessing import filter_by_confidence, non_maximum_suppression, apply_edge_exclusion
    from ctf import CTFEstimator
    from utils import write_star_file, write_confidence_map, generate_statistics_plot
    from storage import StorageManager
    from error_handling import (
        ExitCode, handle_error,
        validate_particle_size, validate_confidence_threshold,
        InputValidationError, FileIOError, ModelError, ProcessingError
    )
    from logging_config import setup_logging, get_logger


def parse_arguments():
    """
    Parse command line arguments with validation.
    
    Returns:
        Namespace containing all configuration parameters
    """
    parser = argparse.ArgumentParser(
        description='ML-based particle picking and CTF estimation for CryoEM',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Required arguments
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input micrograph file (MRC format)'
    )

    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output coordinate file (STAR format)'
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
        help='Batch size for inference (higher = faster but more memory)'
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

    # Optional outputs
    parser.add_argument(
        '--output_confidence_map',
        type=str,
        default=None,
        help='Output confidence heatmap (PNG)'
    )

    parser.add_argument(
        '--output_statistics',
        type=str,
        default=None,
        help='Output statistics plot (PNG)'
    )

    parser.add_argument(
        '--use_plotly',
        action='store_true',
        help='Use Plotly for heatmap (default: Matplotlib/Seaborn)'
    )

    # Storage configuration
    parser.add_argument(
        '--storage_config',
        type=str,
        default=None,
        help='Path to storage configuration file (YAML)'
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


def main():
    """
    Main execution function.
    Orchestrates the full pipeline: load → preprocess → detect → filter → CTF → write outputs
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Parse arguments
    args = parse_arguments()
    
    # Set up logging
    logger = setup_logging(verbose=args.verbose, log_file=args.log_file)
    start_time = time.time()
    
    try:
        # Validate parameters
        logger.info("Validating parameters...")
        validate_particle_size(args.particle_size)
        validate_confidence_threshold(args.confidence_threshold)
        
        # Initialize storage manager
        storage_manager = None
        if args.storage_config:
            logger.info(f"Loading storage configuration: {args.storage_config}")
            storage_manager = StorageManager(args.storage_config)
        
        # Resolve input path
        input_path = args.input
        if storage_manager:
            input_path = storage_manager.resolve_path(args.input)
        
        logger.info(f"Loading micrograph: {input_path}")
        
        # Load micrograph (memory-mapped)
        micrograph = load_micrograph_mmap(input_path)
        logger.info(f"Micrograph shape: {micrograph.shape}")
        
        # Fast normalization (Numba-accelerated)
        logger.info("Normalizing micrograph...")
        micrograph_norm = normalize_micrograph(micrograph)
        
        # Load YOLOv8n model (cached for repeated calls)
        model_path = args.model_path
        if model_path is None:
            # Use default YOLOv8n model (pretrained or fine-tuned)
            try:
                from lib.ml_model.picker import get_default_model_path
            except ImportError:
                from ml_model.picker import get_default_model_path
            model_path = get_default_model_path()
        
        logger.info(f"Loading YOLOv8n model: {model_path}")
        model = load_model_cached(model_path, device=args.device)
        
        # Initialize inference engine
        logger.info("Initializing inference engine...")
        engine = FastInferenceEngine(
            model,
            device=args.device,
            use_amp=(args.device == 'cuda')
        )
        engine.batch_size = args.batch_size
        
        # Run YOLOv8n prediction
        logger.info("Running YOLOv8n particle detection...")
        coords, confidences = engine.predict_micrograph(
            micrograph_norm,
            particle_size=args.particle_size,
            conf_threshold=args.confidence_threshold * 0.5  # YOLO uses lower threshold for initial detection
        )
        
        logger.info(f"Initial detections: {len(coords)} particles")
        
        # Apply post-processing filters
        logger.info("Applying post-processing filters...")
        
        # 1. Confidence threshold filtering
        coords, confidences = filter_by_confidence(
            coords, confidences, args.confidence_threshold
        )
        logger.info(f"After confidence filtering: {len(coords)} particles")
        
        # 2. Non-maximum suppression
        min_distance = args.min_distance if args.min_distance else args.particle_size
        coords, confidences = non_maximum_suppression(
            coords, confidences, min_distance
        )
        logger.info(f"After NMS: {len(coords)} particles")
        
        # 3. Edge exclusion
        if args.edge_exclusion > 0:
            coords, confidences = apply_edge_exclusion(
                coords, confidences, micrograph.shape, args.edge_exclusion
            )
            logger.info(f"After edge exclusion: {len(coords)} particles")
        
        # CTF estimation (if requested)
        ctf_params = None
        if args.ctf_estimation:
            logger.info("Estimating CTF parameters...")
            ctf_estimator = CTFEstimator(
                voltage=args.voltage,
                cs=args.cs,
                pixel_size=args.pixel_size
            )
            ctf_params = ctf_estimator.estimate(micrograph)
            
            logger.info(f"CTF Results:")
            logger.info(f"  Defocus: {ctf_params.average_defocus():.2f} μm")
            logger.info(f"  Astigmatism: {ctf_params.astigmatism:.2f} Å")
            logger.info(f"  Fit resolution: {ctf_params.fit_resolution:.2f} Å")
            logger.info(f"  Max resolution: {ctf_params.max_resolution:.2f} Å")
            logger.info(f"  Fit quality: {ctf_params.fit_quality:.3f}")
        
        # Write outputs
        logger.info(f"Writing STAR file: {args.output}")
        write_star_file(
            args.output,
            coords,
            confidences,
            ctf_params=ctf_params,
            micrograph_name=Path(args.input).name
        )
        
        # Optional: confidence heatmap
        if args.output_confidence_map:
            logger.info(f"Generating confidence heatmap: {args.output_confidence_map}")
            write_confidence_map(
                args.output_confidence_map,
                micrograph.shape,
                coords,
                confidences,
                use_plotly=args.use_plotly
            )
        
        # Optional: statistics plot
        if args.output_statistics:
            logger.info(f"Generating statistics plot: {args.output_statistics}")
            generate_statistics_plot(
                coords,
                confidences,
                args.output_statistics
            )
        
        # Report statistics
        elapsed = time.time() - start_time
        
        logger.info("\n" + "="*50)
        logger.info("Processing Complete!")
        logger.info("="*50)
        logger.info(f"Particles detected: {len(coords)}")
        logger.info(f"Mean confidence: {confidences.mean():.3f}")
        logger.info(f"Std confidence: {confidences.std():.3f}")
        logger.info(f"Processing time: {elapsed:.2f}s")
        logger.info("="*50)
        
        return ExitCode.SUCCESS
        
    except InputValidationError as e:
        handle_error(e, ExitCode.INPUT_VALIDATION_ERROR)
    except FileIOError as e:
        handle_error(e, ExitCode.FILE_IO_ERROR)
    except ModelError as e:
        handle_error(e, ExitCode.MODEL_ERROR)
    except ProcessingError as e:
        handle_error(e, ExitCode.PROCESSING_ERROR)
    except Exception as e:
        # Unexpected error
        logger.exception("Unexpected error occurred")
        print(f"ERROR: Unexpected error - {str(e)}", file=sys.stderr)
        return ExitCode.PROCESSING_ERROR


if __name__ == '__main__':
    sys.exit(main())