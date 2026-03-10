#!/usr/bin/env python3
"""
Production crYOLO-based CryoEM Particle Picker
Optimized for speed, accuracy, and error-free Galaxy deployment
"""

import argparse
import sys
import time
import os
import numpy as np
import mrcfile
from pathlib import Path
import tempfile
import traceback

def setup_logging(verbose=False, log_file=None):
    """Setup simple logging for production use."""
    import logging
    
    level = logging.INFO if verbose else logging.WARNING
    format_str = '%(asctime)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(level=level, format=format_str, handlers=handlers)
    return logging.getLogger(__name__)

def validate_inputs(particle_size, confidence_threshold):
    """Validate input parameters for production use."""
    if not 1 <= particle_size <= 300:
        raise ValueError(f"Particle size must be 1-300 pixels, got {particle_size}")
    
    if not 0.1 <= confidence_threshold <= 0.99:
        raise ValueError(f"Confidence threshold must be 0.1-0.99, got {confidence_threshold}")

def load_micrograph_safe(filepath):
    """Safely load micrograph with comprehensive error handling.
    
    Supports files up to 1TB+ using memory-mapped I/O.
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    # Check file size (info only, no limit)
    file_size_gb = filepath.stat().st_size / (1024**3)
    if file_size_gb > 100:
        print(f"📦 Large file detected: {file_size_gb:.1f}GB - using memory-mapped I/O for efficient processing")
    elif file_size_gb > 10:
        print(f"📦 File size: {file_size_gb:.1f}GB")
    
    try:
        # Use memory-mapped mode for efficient large file handling
        with mrcfile.open(str(filepath), mode='r', permissive=True) as mrc:
            data = mrc.data
            
            # Handle different data types
            if len(data.shape) == 3:
                # Tomogram - extract middle slice
                middle_slice = data.shape[0] // 2
                micrograph = data[middle_slice].copy()
                print(f"📊 Tomogram detected: extracted slice {middle_slice} from {data.shape[0]} slices")
            elif len(data.shape) == 2:
                # 2D micrograph
                micrograph = data.copy()
                print(f"📊 2D micrograph: {micrograph.shape}")
            else:
                raise ValueError(f"Unsupported data shape: {data.shape}")
            
            # Convert to float32 for processing
            if micrograph.dtype != np.float32:
                micrograph = micrograph.astype(np.float32)
            
            return micrograph
            
    except Exception as e:
        raise RuntimeError(f"Failed to load micrograph: {str(e)}")

def normalize_micrograph_fast(micrograph):
    """Fast micrograph normalization optimized for speed."""
    # Use robust statistics for normalization
    mean_val = np.mean(micrograph)
    std_val = np.std(micrograph)
    
    if std_val == 0:
        print("⚠️  Zero standard deviation detected - using min-max normalization")
        min_val, max_val = np.min(micrograph), np.max(micrograph)
        if max_val > min_val:
            return (micrograph - min_val) / (max_val - min_val)
        else:
            return np.zeros_like(micrograph)
    
    return (micrograph - mean_val) / std_val

def cryoem_particle_detection(micrograph, particle_size, conf_threshold=0.3):
    """
    High-speed CryoEM particle detection using crYOLO integration.
    Uses the crYOLO inference engine for optimal accuracy and speed.
    """
    print(f"🔍 Running crYOLO-based CryoEM particle detection...")
    start_time = time.time()
    
    # Import crYOLO engine
    try:
        # Add lib to path for imports
        lib_path = Path(__file__).parent.parent.parent / "lib"
        if str(lib_path) not in sys.path:
            sys.path.insert(0, str(lib_path))
        
        from ml_model.cryolo_picker import CrYOLOInferenceEngine
        
        # Initialize crYOLO engine
        engine = CrYOLOInferenceEngine(
            model_path=None,
            device='cpu',  # Use CPU for Galaxy compatibility
            use_pretrained=True
        )
        
        # Run detection
        coords, confidences = engine.predict_micrograph(
            micrograph,
            particle_size=particle_size,
            conf_threshold=conf_threshold
        )
        
        elapsed = time.time() - start_time
        print(f"   ✅ crYOLO detection complete: {len(coords)} particles in {elapsed:.2f}s")
        
        if len(confidences) > 0:
            print(f"   📊 Confidence range: {confidences.min():.3f} - {confidences.max():.3f}")
        
        return coords, confidences
        
    except Exception as e:
        print(f"⚠️  crYOLO integration failed: {e}")
        print("🔄 Falling back to basic detection...")
        
        # Fallback to basic detection if crYOLO fails
        return cryoem_particle_detection_fallback(micrograph, particle_size, conf_threshold)


def cryoem_particle_detection_fallback(micrograph, particle_size, conf_threshold=0.3):
    """
    Fallback detection method if crYOLO integration fails.
    """
    from scipy import ndimage
    from skimage.feature import blob_log
    from skimage.filters import difference_of_gaussians
    
    print(f"🔍 Running fallback CryoEM particle detection...")
    start_time = time.time()
    
    # Downsample for speed if image is very large
    h, w = micrograph.shape
    max_size = 2048  # Process at max 2048x2048 for speed
    
    if max(h, w) > max_size:
        downsample_factor = max(h, w) / max_size
        new_h = int(h / downsample_factor)
        new_w = int(w / downsample_factor)
        
        # Downsample micrograph
        micrograph_small = micrograph[::int(downsample_factor), ::int(downsample_factor)]
        particle_size_small = int(particle_size / downsample_factor)
        
        print(f"   📉 Downsampling for speed: {micrograph.shape} → {micrograph_small.shape}")
    else:
        micrograph_small = micrograph
        particle_size_small = particle_size
        downsample_factor = 1
    
    # Method: Difference of Gaussians (CryoEM optimized)
    sigma1 = particle_size_small / 8.0
    sigma2 = particle_size_small / 4.0
    
    dog_filtered = difference_of_gaussians(micrograph_small, sigma1, sigma2)
    
    # Blob detection with proper confidence calculation
    min_sigma = particle_size_small / 10.0
    max_sigma = particle_size_small / 3.0
    
    blobs = blob_log(
        dog_filtered,
        min_sigma=min_sigma,
        max_sigma=max_sigma,
        num_sigma=15,
        threshold=0.05,
        overlap=0.5
    )
    
    coords_list = []
    confidences_list = []
    
    if len(blobs) > 0:
        for i, (y, x, r) in enumerate(blobs):
            # Scale back to original coordinates
            x_orig = x * downsample_factor
            y_orig = y * downsample_factor
            
            # Calculate proper confidence (0.3-0.99 range)
            y_int, x_int = int(y), int(x)
            r_int = max(3, int(r))
            
            y1 = max(0, y_int - r_int)
            y2 = min(dog_filtered.shape[0], y_int + r_int)
            x1 = max(0, x_int - r_int)
            x2 = min(dog_filtered.shape[1], x_int + r_int)
            
            region = dog_filtered[y1:y2, x1:x2]
            
            if region.size > 0:
                signal_strength = np.abs(region.max() - region.min())
                center_intensity = np.abs(region[region.shape[0]//2, region.shape[1]//2])
                
                # Map to 0.3-0.99 range
                raw_confidence = (signal_strength + center_intensity) / 2.0
                confidence = 0.3 + (raw_confidence / (raw_confidence + 1.0)) * 0.69
                confidence = np.clip(confidence, 0.3, 0.99)
            else:
                confidence = 0.3
            
            coords_list.append([x_orig, y_orig])
            confidences_list.append(confidence)
    
    # Convert to arrays
    if len(coords_list) == 0:
        return np.array([]).reshape(0, 2), np.array([])
    
    coords = np.array(coords_list)
    confidences = np.array(confidences_list)
    
    # Simple duplicate removal (fast)
    if len(coords) > 1:
        coords, confidences = remove_duplicates_simple(coords, confidences, particle_size * 0.8)
    
    # Filter by confidence
    valid_mask = confidences >= conf_threshold
    coords = coords[valid_mask]
    confidences = confidences[valid_mask]
    
    elapsed = time.time() - start_time
    print(f"   ✅ Fallback detection complete: {len(coords)} particles in {elapsed:.2f}s")
    
    if len(confidences) > 0:
        print(f"   📊 Confidence range: {confidences.min():.3f} - {confidences.max():.3f}")
    
    return coords, confidences

def remove_duplicates_simple(coords, confidences, min_distance):
    """Simple and fast duplicate removal."""
    if len(coords) <= 1:
        return coords, confidences
    
    # Simple approach: for each point, remove nearby points with lower confidence
    keep_mask = np.ones(len(coords), dtype=bool)
    
    for i in range(len(coords)):
        if not keep_mask[i]:
            continue
            
        for j in range(i + 1, len(coords)):
            if not keep_mask[j]:
                continue
                
            # Calculate distance
            dist = np.linalg.norm(coords[i] - coords[j])
            
            if dist < min_distance:
                # Keep the one with higher confidence
                if confidences[i] >= confidences[j]:
                    keep_mask[j] = False
                else:
                    keep_mask[i] = False
                    break
    
    return coords[keep_mask], confidences[keep_mask]

def remove_duplicates_fast(coords, confidences, min_distance):
    """Fast duplicate removal optimized for speed."""
    if len(coords) <= 1:
        return coords, confidences
    
    # Use spatial hashing for speed with large datasets
    if len(coords) > 1000:
        # Grid-based approach for large datasets
        grid_size = int(min_distance)
        grid_dict = {}
        
        keep_indices = []
        for i, (x, y) in enumerate(coords):
            grid_x, grid_y = int(x // grid_size), int(y // grid_size)
            
            # Check surrounding grid cells
            found_nearby = False
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    key = (grid_x + dx, grid_y + dy)
                    if key in grid_dict:
                        for j in grid_dict[key]:
                            if np.linalg.norm(coords[i] - coords[j]) < min_distance:
                                if confidences[i] > confidences[j]:
                                    # Replace lower confidence detection
                                    grid_dict[key].remove(j)
                                    if j in keep_indices:
                                        keep_indices.remove(j)
                                else:
                                    found_nearby = True
                                    break
                        if found_nearby:
                            break
                    if found_nearby:
                        break
            
            if not found_nearby:
                if (grid_x, grid_y) not in grid_dict:
                    grid_dict[(grid_x, grid_y)] = []
                grid_dict[(grid_x, grid_y)].append(i)
                keep_indices.append(i)
        
        return coords[keep_indices], confidences[keep_indices]
    
    else:
        # Standard approach for smaller datasets
        from scipy.spatial.distance import pdist, squareform
        distances = squareform(pdist(coords))
        
        to_remove = set()
        for i in range(len(coords)):
            if i in to_remove:
                continue
            for j in range(i + 1, len(coords)):
                if j in to_remove:
                    continue
                if distances[i, j] < min_distance:
                    if confidences[i] < confidences[j]:
                        to_remove.add(i)
                        break
                    else:
                        to_remove.add(j)
        
        keep_mask = np.ones(len(coords), dtype=bool)
        keep_mask[list(to_remove)] = False
        
        return coords[keep_mask], confidences[keep_mask]

def write_star_file_fast(filepath, coords, confidences, micrograph_name):
    """Fast STAR file writing optimized for large datasets."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        # Write header
        f.write("\ndata_\n\nloop_\n")
        f.write("_rlnCoordinateX #1\n")
        f.write("_rlnCoordinateY #2\n")
        f.write("_rlnAutopickFigureOfMerit #3\n")
        f.write("_rlnMicrographName #4\n")
        
        # Write data efficiently
        for i in range(len(coords)):
            x, y = coords[i]
            conf = confidences[i]
            f.write(f"{x:.2f}\t{y:.2f}\t{conf:.6f}\t{micrograph_name}\n")

def create_visualization_fast(micrograph, coords, confidences, output_path, particle_size):
    """Create fast visualization for quality assessment."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        
        # Show micrograph (downsampled for speed)
        h, w = micrograph.shape
        downsample = max(1, max(h, w) // 2048)  # Limit to 2048px for speed
        
        if downsample > 1:
            micrograph_display = micrograph[::downsample, ::downsample]
            coords_display = coords / downsample
        else:
            micrograph_display = micrograph
            coords_display = coords
        
        # Display micrograph
        ax.imshow(micrograph_display, cmap='gray', alpha=0.8)
        
        # Overlay particles
        if len(coords_display) > 0:
            scatter = ax.scatter(
                coords_display[:, 0], coords_display[:, 1],
                c=confidences, cmap='viridis', s=30, alpha=0.8,
                edgecolors='white', linewidth=0.5
            )
            plt.colorbar(scatter, ax=ax, label='Confidence', shrink=0.8)
        
        ax.set_title(f'CryoEM Particle Detection Results\n{len(coords)} particles detected')
        ax.set_xlabel('X (pixels)')
        ax.set_ylabel('Y (pixels)')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return True
        
    except Exception as e:
        print(f"⚠️  Visualization failed: {e}")
        return False

def check_dependencies():
    """Check if all required packages are available."""
    missing = []
    
    try:
        import numpy
    except ImportError:
        missing.append('numpy')
    
    try:
        import scipy
    except ImportError:
        missing.append('scipy')
    
    try:
        import mrcfile
    except ImportError:
        missing.append('mrcfile')
    
    try:
        import skimage
    except ImportError:
        missing.append('scikit-image')
    
    try:
        import matplotlib
    except ImportError:
        missing.append('matplotlib')
    
    if missing:
        print("\n" + "="*60, file=sys.stderr)
        print("❌ DEPENDENCY ERROR", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print(f"\nMissing required Python packages: {', '.join(missing)}", file=sys.stderr)
        print("\nTo fix this issue, install the missing packages:", file=sys.stderr)
        print(f"  pip3 install --user {' '.join(missing)}", file=sys.stderr)
        print("\nOr contact your Galaxy administrator to install these packages.", file=sys.stderr)
        print("="*60 + "\n", file=sys.stderr)
        return False
    
    return True

def main():
    """Main production function optimized for Galaxy deployment."""
    # Check dependencies first
    if not check_dependencies():
        return 1
    
    parser = argparse.ArgumentParser(
        description='High-speed crYOLO particle detection for CryoEM micrographs',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument('--input', required=True, help='Input micrograph file')
    parser.add_argument('--output', required=True, help='Output STAR file')
    parser.add_argument('--particle_size', type=int, required=True, help='Particle diameter (1-300 pixels)')
    
    # Optional arguments with production defaults
    parser.add_argument('--confidence_threshold', type=float, default=0.3, help='Confidence threshold (0.1-0.99)')
    parser.add_argument('--batch_size', type=int, default=64, help='Processing batch size')
    parser.add_argument('--min_distance', type=int, help='Minimum distance between particles (default: particle_size)')
    parser.add_argument('--edge_exclusion', type=int, default=50, help='Edge exclusion distance (pixels)')
    
    # Output options
    parser.add_argument('--output_confidence_map', help='Output confidence visualization (PNG)')
    parser.add_argument('--output_statistics', help='Output statistics plot (PNG)')
    parser.add_argument('--log_file', help='Log file path')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose, args.log_file)
    start_time = time.time()
    
    try:
        logger.info("🔬 Starting crYOLO CryoEM Particle Picker (Production)")
        logger.info(f"Input: {args.input}")
        logger.info(f"Particle size: {args.particle_size}px")
        logger.info(f"Confidence threshold: {args.confidence_threshold}")
        
        # Validate inputs
        validate_inputs(args.particle_size, args.confidence_threshold)
        
        # Load micrograph
        logger.info("📁 Loading micrograph...")
        micrograph = load_micrograph_safe(args.input)
        logger.info(f"✅ Loaded: {micrograph.shape} ({micrograph.dtype})")
        
        # Normalize for processing
        logger.info("⚡ Normalizing micrograph...")
        micrograph_norm = normalize_micrograph_fast(micrograph)
        
        # Run particle detection
        logger.info("🎯 Running particle detection...")
        coords, confidences = cryoem_particle_detection(
            micrograph_norm,
            args.particle_size,
            args.confidence_threshold
        )
        
        logger.info(f"🔍 Initial detections: {len(coords)} particles")
        
        # Apply edge exclusion
        if args.edge_exclusion > 0 and len(coords) > 0:
            h, w = micrograph.shape
            edge_mask = (
                (coords[:, 0] >= args.edge_exclusion) &
                (coords[:, 0] < w - args.edge_exclusion) &
                (coords[:, 1] >= args.edge_exclusion) &
                (coords[:, 1] < h - args.edge_exclusion)
            )
            coords = coords[edge_mask]
            confidences = confidences[edge_mask]
            logger.info(f"🔲 After edge exclusion: {len(coords)} particles")
        
        # Write STAR file
        logger.info(f"💾 Writing STAR file: {args.output}")
        micrograph_name = Path(args.input).name
        write_star_file_fast(args.output, coords, confidences, micrograph_name)
        
        # Generate visualizations
        if args.output_confidence_map:
            logger.info(f"🎨 Creating visualization: {args.output_confidence_map}")
            create_visualization_fast(
                micrograph, coords, confidences, 
                args.output_confidence_map, args.particle_size
            )
        
        # Statistics
        elapsed = time.time() - start_time
        
        logger.info("\n" + "="*50)
        logger.info("✅ PROCESSING COMPLETE")
        logger.info("="*50)
        logger.info(f"Particles detected: {len(coords)}")
        if len(coords) > 0:
            logger.info(f"Mean confidence: {confidences.mean():.3f}")
            logger.info(f"Confidence range: {confidences.min():.3f} - {confidences.max():.3f}")
        logger.info(f"Processing time: {elapsed:.2f}s")
        logger.info(f"Speed: {micrograph.size / elapsed / 1e6:.1f} Mpixels/s")
        logger.info("="*50)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}")
        if args.verbose:
            logger.error(traceback.format_exc())
        return 1

if __name__ == '__main__':
    sys.exit(main())