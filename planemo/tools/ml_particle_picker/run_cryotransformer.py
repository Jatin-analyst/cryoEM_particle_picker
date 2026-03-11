#!/usr/bin/env python3
"""
CryoTransformer Runner for Galaxy
Uses bundled CryoPPP pre-trained model for particle detection
"""

import argparse
import sys
import os
from pathlib import Path
import numpy as np

def setup_logging():
    """Setup simple logging."""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def setup_model_paths():
    """Setup paths to bundled model files."""
    # Model files are bundled with the tool
    script_dir = Path(__file__).parent.resolve()
    
    # Try multiple possible locations for model and lib directories
    # Location 1: Tool Shed structure (planemo/tools/ml_particle_picker/)
    model_dir_1 = script_dir.parent.parent.parent / "pretrained_model"
    lib_dir_1 = script_dir.parent.parent.parent / "lib"
    
    # Location 2: Galaxy tool directory (flat structure)
    model_dir_2 = script_dir / "pretrained_model"
    lib_dir_2 = script_dir / "lib"
    
    # Location 3: Parent directory
    model_dir_3 = script_dir.parent / "pretrained_model"
    lib_dir_3 = script_dir.parent / "lib"
    
    # Check which location exists
    model_dir = None
    lib_dir = None
    
    for md, ld in [(model_dir_1, lib_dir_1), (model_dir_2, lib_dir_2), (model_dir_3, lib_dir_3)]:
        main_model = md / "CryoTransformer_pretrained_model.pth"
        model_imp = ld / "model_imp_file"
        if main_model.exists() and model_imp.exists():
            model_dir = md
            lib_dir = ld
            break
    
    if model_dir is None or lib_dir is None:
        logger.error(f"❌ Could not find model or lib directory")
        logger.error(f"Script directory: {script_dir}")
        logger.error(f"Tried locations:")
        logger.error(f"  1. {model_dir_1} / {lib_dir_1}")
        logger.error(f"  2. {model_dir_2} / {lib_dir_2}")
        logger.error(f"  3. {model_dir_3} / {lib_dir_3}")
        raise FileNotFoundError(f"CryoTransformer model and lib directories not found")
    
    main_model = model_dir / "CryoTransformer_pretrained_model.pth"
    logger.info(f"✅ Using bundled CryoTransformer model: {main_model}")
    logger.info(f"✅ Model architecture from: {lib_dir / 'model_imp_file'}")
    
    return model_dir, lib_dir

def check_dependencies():
    """Check if required packages are available."""
    missing = []
    
    packages = {
        'torch': 'torch',
        'numpy': 'numpy',
        'mrcfile': 'mrcfile',
        'scipy': 'scipy',
        'PIL': 'pillow',
        'torchvision': 'torchvision'
    }
    
    for import_name, package_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        logger.error("\n" + "="*60)
        logger.error("❌ DEPENDENCY ERROR")
        logger.error("="*60)
        logger.error(f"\nMissing required Python packages: {', '.join(missing)}")
        logger.error("\nTo fix this issue, install the missing packages:")
        logger.error(f"  pip3 install --user {' '.join(missing)}")
        logger.error("\nOr contact your Galaxy administrator to install these packages.")
        logger.error("="*60 + "\n")
        return False
    
    return True


class ModelArgs:
    """Arguments for building CryoTransformer model."""
    def __init__(self):
        # Model architecture
        self.backbone = 'resnet152'
        self.dilation = True
        self.position_embedding = 'sine'
        
        # Transformer
        self.enc_layers = 6
        self.dec_layers = 6
        self.dim_feedforward = 2048
        self.hidden_dim = 256
        self.dropout = 0.1
        self.nheads = 8
        self.pre_norm = False
        self.num_queries = 600
        
        # Training (not used for inference)
        self.lr_backbone = 1e-5
        self.masks = False
        self.aux_loss = True
        self.dataset_file = 'micrograph'
        self.device = 'cpu'
        
        # Loss coefficients (not used for inference)
        self.set_cost_class = 1
        self.set_cost_bbox = 5
        self.set_cost_giou = 2
        self.bbox_loss_coef = 5
        self.giou_loss_coef = 2
        self.eos_coef = 0.1
        self.mask_loss_coef = 1
        self.dice_loss_coef = 1
        
        # Frozen weights
        self.frozen_weights = None

def run_cryotransformer_prediction(input_mrc, output_star, model_dir, lib_dir,
                                   particle_size, confidence_threshold, gpu_id=-1):
    """Run CryoTransformer prediction."""
    logger.info("🔬 Running CryoTransformer particle detection...")
    
    import torch
    import mrcfile
    import numpy as np
    
    try:
        
        # Add lib directory to path to import model modules
        sys.path.insert(0, str(lib_dir))
        from model_imp_file import build_model
        
        # Setup device
        device = torch.device('cuda' if gpu_id >= 0 and torch.cuda.is_available() else 'cpu')
        logger.info(f"🖥️  Using device: {device}")
        
        # Build model architecture
        logger.info("📂 Building CryoTransformer model architecture...")
        args = ModelArgs()
        args.device = str(device)
        
        model, _, _ = build_model(args)
        
        # Load pre-trained weights
        logger.info(f"📂 Loading pre-trained weights from {model_dir}")
        main_model_path = model_dir / "CryoTransformer_pretrained_model.pth"
        
        checkpoint = torch.load(main_model_path, map_location=device, weights_only=False)
        
        # Extract state dict from checkpoint
        if isinstance(checkpoint, dict) and 'model' in checkpoint:
            state_dict = checkpoint['model']
            logger.info(f"✅ Loaded checkpoint (epoch: {checkpoint.get('epoch', 'unknown')})")
        else:
            state_dict = checkpoint
        
        # Load state dict into model
        model.load_state_dict(state_dict)
        model.to(device)
        model.eval()
        
        logger.info("✅ Model loaded successfully")
        
        # Load micrograph
        logger.info(f"📁 Loading micrograph: {input_mrc}")
        with mrcfile.open(input_mrc, permissive=True) as mrc:
            data = mrc.data
            
            if data is None:
                raise ValueError(f"Failed to read data from {input_mrc}")
            
            # Handle 3D tomograms - extract middle slice
            if len(data.shape) == 3:
                middle_slice = data.shape[0] // 2
                micrograph = data[middle_slice]
                logger.info(f"📊 Tomogram detected: extracted slice {middle_slice}")
            else:
                micrograph = data
        
        # Get image dimensions
        h, w = micrograph.shape
        logger.info(f"📐 Original image size: {w}x{h}")
        
        # Downsample if image is too large (CryoTransformer was trained on smaller images)
        max_size = 1024  # Maximum dimension
        if max(h, w) > max_size:
            scale_factor = max_size / max(h, w)
            new_h = int(h * scale_factor)
            new_w = int(w * scale_factor)
            
            from scipy.ndimage import zoom
            micrograph_resized = zoom(micrograph, (new_h / h, new_w / w), order=1)
            logger.info(f"📐 Downsampled to: {new_w}x{new_h} (scale: {scale_factor:.3f})")
            
            # Use resized image for prediction
            micrograph_for_pred = micrograph_resized
            pred_h, pred_w = new_h, new_w
        else:
            micrograph_for_pred = micrograph
            pred_h, pred_w = h, w
            scale_factor = 1.0
        
        # Normalize micrograph
        micrograph_for_pred = (micrograph_for_pred - micrograph_for_pred.mean()) / (micrograph_for_pred.std() + 1e-8)
        
        # Convert to RGB (CryoTransformer expects 3-channel input)
        micrograph_rgb = np.stack([micrograph_for_pred, micrograph_for_pred, micrograph_for_pred], axis=0)
        
        # Run prediction
        logger.info("🎯 Running prediction...")
        with torch.no_grad():
            # Convert to tensor [batch, channels, height, width]
            img_tensor = torch.from_numpy(micrograph_rgb).float().unsqueeze(0).to(device)
            
            # Run model
            outputs = model(img_tensor)
            
            # Extract predictions
            pred_logits = outputs['pred_logits'].cpu()
            pred_boxes = outputs['pred_boxes'].cpu()
        
        # Process predictions
        # Get confidence scores using sigmoid (as in predict.py)
        probas = pred_logits.sigmoid()
        topk_values, topk_indexes = torch.topk(probas.view(pred_logits.shape[0], -1), 
                                                args.num_queries, dim=1)
        scores = topk_values[0]
        
        # Filter by quartile threshold (as in predict.py)
        quartile_threshold = 0.25
        keep = scores > np.quantile(scores.numpy(), quartile_threshold)
        
        # Get boxes and scores for kept predictions
        boxes_normalized = pred_boxes[0, keep]
        confidences = scores[keep].numpy()
        
        # Convert normalized boxes [cx, cy, w, h] to pixel coordinates [x1, y1, x2, y2]
        # Scale back to original image size
        boxes_pixel = []
        for box in boxes_normalized:
            cx, cy, bw, bh = box
            # Convert to original image coordinates
            x1 = ((cx - bw/2) * pred_w) / scale_factor
            y1 = ((cy - bh/2) * pred_h) / scale_factor
            x2 = ((cx + bw/2) * pred_w) / scale_factor
            y2 = ((cy + bh/2) * pred_h) / scale_factor
            boxes_pixel.append([x1.item(), y1.item(), x2.item(), y2.item()])
        
        boxes_pixel = np.array(boxes_pixel)
        
        # Apply NMS (Non-Maximum Suppression)
        nms_threshold = 0.7
        if len(boxes_pixel) > 0:
            boxes_final, confidences_final = nms(boxes_pixel, confidences, nms_threshold)
        else:
            boxes_final = boxes_pixel
            confidences_final = confidences
        
        logger.info(f"✅ Detection complete: {len(boxes_final)} particles found")
        
        # Write STAR file
        write_star_file(output_star, boxes_final, confidences_final, Path(input_mrc).name, h)
        
        return len(boxes_final)
        
    except Exception as e:
        logger.error(f"❌ Prediction failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def nms(bounding_boxes, confidence_scores, nms_threshold):
    """Non-Maximum Suppression to remove overlapping boxes."""
    if len(bounding_boxes) == 0:
        return np.array([]), np.array([])

    boxes = np.array(bounding_boxes)
    scores = np.array(confidence_scores)

    # Coordinates of bounding boxes
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    # Compute areas
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)

    # Sort by confidence score
    order = np.argsort(scores)

    keep_boxes = []
    keep_scores = []

    while order.size > 0:
        # Pick box with highest score
        idx = order[-1]
        keep_boxes.append(bounding_boxes[idx])
        keep_scores.append(confidence_scores[idx])

        # Compute IoU with remaining boxes
        xx1 = np.maximum(x1[idx], x1[order[:-1]])
        yy1 = np.maximum(y1[idx], y1[order[:-1]])
        xx2 = np.minimum(x2[idx], x2[order[:-1]])
        yy2 = np.minimum(y2[idx], y2[order[:-1]])

        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        intersection = w * h

        iou = intersection / (areas[idx] + areas[order[:-1]] - intersection)

        # Keep boxes with IoU less than threshold
        inds = np.where(iou < nms_threshold)[0]
        order = order[inds]

    return np.array(keep_boxes), np.array(keep_scores)

def write_star_file(filepath, boxes, confidences, micrograph_name, img_height):
    """Write coordinates to STAR file format (RELION/CryoSPARC compatible)."""
    logger.info(f"💾 Writing STAR file: {filepath}")
    
    with open(filepath, 'w') as f:
        # Write header
        f.write("\ndata_\n\nloop_\n")
        f.write("_rlnMicrographName #1\n")
        f.write("_rlnCoordinateX #2\n")
        f.write("_rlnCoordinateY #3\n")
        f.write("_rlnClassNumber #4\n")
        f.write("_rlnAnglePsi #5\n")
        f.write("_rlnAutopickFigureOfMerit #6\n")
        
        # Write data
        for i in range(len(boxes)):
            box = boxes[i]
            conf = confidences[i]
            
            # Calculate center coordinates
            # box format: [x1, y1, x2, y2]
            center_x = (box[0] + box[2]) / 2
            center_y = (box[1] + box[3]) / 2
            
            # Flip Y coordinate for CryoSPARC orientation
            center_y_flipped = img_height - center_y
            
            f.write(f"{micrograph_name}\t{center_x:.2f}\t{center_y_flipped:.2f}\t-9999\t-9999\t{conf:.6f}\n")
    
    logger.info(f"✅ STAR file written: {len(boxes)} particles")

def main():
    parser = argparse.ArgumentParser(
        description='CryoTransformer particle detection for CryoEM micrographs'
    )
    
    parser.add_argument('--input', required=True, help='Input micrograph file (MRC/MRCS/ST)')
    parser.add_argument('--output', required=True, help='Output STAR file')
    parser.add_argument('--particle_size', type=int, required=True, help='Particle diameter (pixels)')
    parser.add_argument('--confidence_threshold', type=float, default=0.3, help='Confidence threshold')
    parser.add_argument('--gpu_id', type=int, default=-1, help='GPU ID (-1 for CPU)')
    parser.add_argument('--log_file', help='Log file path')
    
    args = parser.parse_args()
    
    try:
        logger.info("🔬 Starting CryoTransformer Particle Picker")
        logger.info(f"Input: {args.input}")
        logger.info(f"Particle size: {args.particle_size}px")
        logger.info(f"Confidence threshold: {args.confidence_threshold}")
        logger.info(f"Script location: {Path(__file__).resolve()}")
        logger.info(f"Working directory: {Path.cwd()}")
        
        # Check dependencies
        logger.info("Checking dependencies...")
        if not check_dependencies():
            logger.error("❌ Dependency check failed")
            return 1
        logger.info("✅ All dependencies available")
        
        # Setup model paths
        logger.info("Setting up model paths...")
        try:
            model_dir, lib_dir = setup_model_paths()
        except Exception as e:
            logger.error(f"❌ Failed to setup model paths: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 1
        
        # Run prediction
        logger.info("Starting prediction...")
        num_particles = run_cryotransformer_prediction(
            args.input,
            args.output,
            model_dir,
            lib_dir,
            args.particle_size,
            args.confidence_threshold,
            args.gpu_id
        )
        
        logger.info("\n" + "="*50)
        logger.info("✅ PROCESSING COMPLETE")
        logger.info("="*50)
        logger.info(f"Particles detected: {num_particles}")
        logger.info(f"Output: {args.output}")
        logger.info("="*50)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == '__main__':
    sys.exit(main())
