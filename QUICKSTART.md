# Quick Start Guide - CryoEM Precision Tool with YOLOv8n

Get started with particle picking in 5 minutes!

## Installation

```bash
# Clone repository (if not already done)
git clone https://github.com/your-org/cryoem-precision-tool.git
cd cryoem-precision-tool

# Install dependencies
pip install -r requirements.txt

# Test installation
python training/test_installation.py
```

## Option 1: Use Pretrained Model (No Training)

Perfect for quick testing or if you don't have training data yet.

```bash
# Basic usage
python planemo/tools/ml_particle_picker/ml_picker.py \
    --input your_micrograph.mrc \
    --output particles.star \
    --particle_size 200 \
    --confidence_threshold 0.7 \
    --device cuda

# With CTF estimation and visualizations
python planemo/tools/ml_particle_picker/ml_picker.py \
    --input your_micrograph.mrc \
    --output particles.star \
    --particle_size 200 \
    --confidence_threshold 0.7 \
    --ctf_estimation \
    --voltage 300 \
    --cs 2.7 \
    --pixel_size 1.0 \
    --output_confidence_map heatmap.png \
    --output_statistics stats.png \
    --device cuda \
    --verbose
```

**Note**: Pretrained model will be downloaded automatically (~6MB).

## Option 2: Train Custom Model (Recommended)

For best results on your specific data.

### Step 1: Organize Your Data

```
data/
├── micrographs/          # Your MRC files
│   ├── mic_001.mrc
│   ├── mic_002.mrc
│   └── ...
└── coordinates/          # Your coordinate files
    ├── mic_001.star      # STAR format
    ├── mic_002.txt       # or text format (x y per line)
    └── ...
```

### Step 2: Prepare Data for YOLO

```bash
python training/prepare_data.py \
    --micrographs_dir data/micrographs \
    --coordinates_dir data/coordinates \
    --output_dir yolo_dataset \
    --particle_size 200 \
    --train_split 0.8 \
    --val_split 0.1
```

This creates:
```
yolo_dataset/
├── data.yaml           # YOLO configuration
├── train/              # 80% of data
├── val/                # 10% of data
└── test/               # 10% of data
```

### Step 3: Train Model

```bash
# GPU training (recommended)
python training/train_model.py \
    --data_yaml yolo_dataset/data.yaml \
    --epochs 100 \
    --batch_size 16 \
    --device cuda

# CPU training (slower)
python training/train_model.py \
    --data_yaml yolo_dataset/data.yaml \
    --epochs 50 \
    --batch_size 4 \
    --device cpu
```

Training outputs saved to `runs/detect/train/`:
- `weights/best.pt` - Best model (use this!)
- `weights/last.pt` - Last epoch
- `results.png` - Training curves
- `confusion_matrix.png` - Performance metrics

### Step 4: Use Trained Model

```bash
python planemo/tools/ml_particle_picker/ml_picker.py \
    --input your_micrograph.mrc \
    --output particles.star \
    --particle_size 200 \
    --model_path runs/detect/train/weights/best.pt \
    --confidence_threshold 0.7 \
    --device cuda
```

## Understanding Parameters

### Essential Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--input` | Input micrograph (MRC) | `micrograph.mrc` |
| `--output` | Output STAR file | `particles.star` |
| `--particle_size` | Particle diameter in pixels | `200` |

### Model Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--model_path` | Custom model path | Pretrained YOLOv8n |
| `--confidence_threshold` | Detection threshold (0.1-0.99) | `0.7` |
| `--device` | cpu or cuda | `cpu` |

### Post-Processing

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--min_distance` | Min distance between particles | `particle_size` |
| `--edge_exclusion` | Exclude particles near edges (pixels) | `0` |

### CTF Estimation

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--ctf_estimation` | Enable CTF estimation | Disabled |
| `--voltage` | Acceleration voltage (kV) | `300.0` |
| `--cs` | Spherical aberration (mm) | `2.7` |
| `--pixel_size` | Pixel size (Å/pixel) | `1.0` |

### Outputs

| Parameter | Description |
|-----------|-------------|
| `--output_confidence_map` | Save heatmap PNG |
| `--output_statistics` | Save statistics plot PNG |
| `--use_plotly` | Use Plotly (interactive) |

## Common Workflows

### Workflow 1: Quick Test

```bash
# Test on one micrograph with pretrained model
python planemo/tools/ml_particle_picker/ml_picker.py \
    --input test.mrc \
    --output test_particles.star \
    --particle_size 200 \
    --device cuda \
    --verbose
```

### Workflow 2: Batch Processing

```bash
# Process multiple micrographs
for mrc in data/micrographs/*.mrc; do
    base=$(basename "$mrc" .mrc)
    python planemo/tools/ml_particle_picker/ml_picker.py \
        --input "$mrc" \
        --output "output/${base}_particles.star" \
        --particle_size 200 \
        --model_path runs/detect/train/weights/best.pt \
        --device cuda
done
```

### Workflow 3: Full Pipeline with CTF

```bash
python planemo/tools/ml_particle_picker/ml_picker.py \
    --input micrograph.mrc \
    --output particles.star \
    --particle_size 200 \
    --model_path runs/detect/train/weights/best.pt \
    --confidence_threshold 0.7 \
    --min_distance 200 \
    --edge_exclusion 50 \
    --ctf_estimation \
    --voltage 300 \
    --cs 2.7 \
    --pixel_size 1.0 \
    --output_confidence_map heatmap.png \
    --output_statistics stats.png \
    --device cuda \
    --verbose
```

## Troubleshooting

### Issue: "ultralytics not found"
```bash
pip install ultralytics
```

### Issue: "No particles detected"
- Lower confidence threshold: `--confidence_threshold 0.5`
- Check particle size is correct
- Train custom model on your data

### Issue: "Too many false positives"
- Increase confidence threshold: `--confidence_threshold 0.8`
- Increase min_distance: `--min_distance 250`
- Add edge exclusion: `--edge_exclusion 100`

### Issue: "Out of memory"
- Use CPU: `--device cpu`
- Process smaller regions
- Close other applications

### Issue: "Training is slow"
- Use GPU: `--device cuda`
- Reduce epochs: `--epochs 50`
- Reduce batch size: `--batch_size 8`

## Performance Expectations

### Inference Speed
- **GPU**: 2-5 seconds per 4k×4k micrograph
- **CPU**: 10-20 seconds per 4k×4k micrograph

### Accuracy (After Training)
- **mAP50**: >0.70 (good), >0.85 (excellent)
- **Precision**: >0.80 (good), >0.90 (excellent)
- **Recall**: >0.75 (good), >0.85 (excellent)

### Training Time (100 epochs)
- **GPU (8GB)**: 1-2 hours for 500 micrographs
- **GPU (16GB)**: 2-4 hours for 1000 micrographs
- **CPU**: 12-24 hours for 500 micrographs

## Data Requirements

| Dataset Size | Use Case | Expected Performance |
|--------------|----------|---------------------|
| 50-100 micrographs | Testing, proof of concept | Basic functionality |
| 500-1000 micrographs | Production use | Good performance |
| 2000+ micrographs | High-quality production | Excellent performance |

## Output Files

### STAR File Format
```
data_

loop_
_rlnCoordinateX
_rlnCoordinateY
_rlnAutopickFigureOfMerit
1234.5  2345.6  0.95
1456.7  2567.8  0.87
...
```

Compatible with:
- RELION
- CryoSPARC
- cisTEM
- Other CryoEM software

### Visualizations
- **Heatmap**: Particle locations colored by confidence
- **Statistics**: Confidence distribution histogram

## Next Steps

1. **Test installation**: `python training/test_installation.py`
2. **Try pretrained model**: Use on sample micrograph
3. **Prepare training data**: Organize micrographs and coordinates
4. **Train custom model**: Follow steps above
5. **Validate results**: Check output STAR files and visualizations
6. **Integrate with Galaxy**: Use Galaxy XML tool definition

## Documentation

- **This Guide**: Quick start (you are here)
- **Training Guide**: `training/TRAINING_GUIDE.md` (comprehensive)
- **Training README**: `training/README.md` (quick reference)
- **Integration Details**: `YOLOV8N_INTEGRATION.md`
- **Main README**: `README.md`

## Getting Help

1. Check `training/TRAINING_GUIDE.md` troubleshooting section
2. Review YOLOv8 docs: https://docs.ultralytics.com/
3. Open issue on GitHub
4. Contact support

## Tips for Success

1. ✅ **Start with pretrained model** - Test before training
2. ✅ **Use GPU if available** - Much faster
3. ✅ **Verify particle size** - Critical parameter
4. ✅ **Check data quality** - Good annotations = good results
5. ✅ **Train on diverse data** - Better generalization
6. ✅ **Validate visually** - Always inspect results
7. ✅ **Iterate on threshold** - Adjust for your data

## Example Session

```bash
# 1. Test installation
python training/test_installation.py

# 2. Quick test with pretrained model
python planemo/tools/ml_particle_picker/ml_picker.py \
    --input sample.mrc \
    --output sample_particles.star \
    --particle_size 200 \
    --device cuda \
    --verbose

# 3. Prepare training data
python training/prepare_data.py \
    --micrographs_dir data/micrographs \
    --coordinates_dir data/coordinates \
    --output_dir yolo_dataset \
    --particle_size 200

# 4. Train model
python training/train_model.py \
    --data_yaml yolo_dataset/data.yaml \
    --epochs 100 \
    --batch_size 16 \
    --device cuda

# 5. Use trained model
python planemo/tools/ml_particle_picker/ml_picker.py \
    --input production.mrc \
    --output production_particles.star \
    --particle_size 200 \
    --model_path runs/detect/train/weights/best.pt \
    --device cuda
```

---

**Ready to start?** Run `python training/test_installation.py` to verify your setup!
