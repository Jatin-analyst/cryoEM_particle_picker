# CryoEM Precision Tool

ML-based particle picking for CryoEM micrographs using **YOLOv8n**, designed for Galaxy Framework.

## Quick Start

### Option 1: Batch Processing (Recommended for 1TB+ datasets)

Process entire directories of micrographs:

```bash
./run_batch_picker.sh \
    --input_dir /path/to/micrographs \
    --output_dir /path/to/output \
    --particle_size 200 \
    --device cuda \
    --recursive \
    --summary_report batch_report.json
```

**See**: [BATCH_PROCESSING_GUIDE.md](BATCH_PROCESSING_GUIDE.md) for complete guide

### Option 2: Single File Processing

### Option 2: Single File Processing

Use pretrained model on single micrograph:

```bash
pip install -r requirements.txt

python planemo/tools/ml_particle_picker/ml_picker.py \
    --input micrograph.mrc \
    --output particles.star \
    --particle_size 200 \
    --device cuda
```

### Option 3: Train Locally (Advanced)

```bash
# 1. Prepare data
python training/prepare_data.py \
    --micrographs_dir data/micrographs \
    --coordinates_dir data/coordinates \
    --output_dir yolo_dataset \
    --particle_size 200

# 2. Train
python training/train_model.py \
    --data_yaml yolo_dataset/data.yaml \
    --epochs 100 \
    --device cuda

# 3. Use trained model
python planemo/tools/ml_particle_picker/ml_picker.py \
    --input micrograph.mrc \
    --output particles.star \
    --particle_size 200 \
    --model_path runs/detect/train/weights/best.pt
```

## Features

- **Batch Processing**: Process 1TB+ datasets efficiently
- **YOLOv8n Detection**: Fast, accurate particle picking
- **Pretrained Weights**: Works out of the box
- **Easy Training**: Fine-tune on your data
- **CTF Estimation**: Integrated CTF parameter estimation
- **Galaxy Integration**: Complete XML tool definition
- **Error Resilience**: Batch processing continues on failures
- **Progress Tracking**: Real-time progress and summary reports

## Documentation

### Essential Guides
- **[BATCH_PROCESSING_GUIDE.md](BATCH_PROCESSING_GUIDE.md)** - Process 1TB+ datasets
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute quick start
- **[GALAXY_DEPLOYMENT_GUIDE.md](GALAXY_DEPLOYMENT_GUIDE.md)** - Galaxy deployment
- **[SYSTEM_REQUIREMENTS.md](SYSTEM_REQUIREMENTS.md)** - Performance and limits
- **[DEPLOYMENT_READY.md](DEPLOYMENT_READY.md)** - Deployment status

## Requirements

- Python 3.8+
- PyTorch 1.13+
- ultralytics 8.0+ (YOLOv8)
- mrcfile, numpy, scipy
- GPU recommended (CPU supported)

## Installation

```bash
git clone https://github.com/your-org/cryoem-precision-tool.git
cd cryoem-precision-tool
pip install -r requirements.txt
```

## Performance

- **Speed**: 2-5 seconds per micrograph (GPU), ~1800 files/hour
- **Batch Processing**: Process 1TB+ datasets efficiently
- **Memory**: ~200-500 MB per file (safe for large datasets)
- **Accuracy**: mAP50 >0.70 (after training)
- **Dataset**: Works with 50+ micrographs

## What This Tool Does

✅ Particle picking (identifies particle locations)
✅ Batch processing (1TB+ datasets)
✅ Outputs STAR files with coordinates
✅ CTF estimation (optional)
✅ Fast inference
✅ Error-resilient processing
✅ Progress tracking and reports
✅ Trainable on custom data

## What This Tool Does NOT Do

❌ 3D reconstruction (use RELION/CryoSPARC)
❌ Motion correction (use MotionCor2)
❌ Final resolution assessment

**Note**: For CTF targets (defocus range, fit resolution), integrate with full CryoEM pipeline (RELION/CryoSPARC).

## Project Structure

```
.
├── README.md                          # This file
├── BATCH_PROCESSING_GUIDE.md         # Batch processing guide
├── QUICKSTART.md                      # Quick start
├── GALAXY_DEPLOYMENT_GUIDE.md        # Galaxy deployment
├── SYSTEM_REQUIREMENTS.md            # Performance specs
├── requirements.txt                   # Dependencies
├── run_picker.sh                      # Single file script
├── run_batch_picker.sh               # Batch processing script
├── lib/
│   ├── ml_model/                     # YOLOv8n model
│   ├── preprocessing/                # Data preprocessing
│   ├── postprocessing/               # Result filtering
│   ├── ctf/                          # CTF estimation
│   ├── batch_processing.py           # Batch processor
│   └── utils/                        # File I/O
└── planemo/tools/ml_particle_picker/
    ├── ml_picker.py                  # Main CLI
    ├── ml_picker_batch.py            # Batch CLI
    └── ml_particle_picker.xml        # Galaxy tool
```

## Support

- Check documentation: [BATCH_PROCESSING_GUIDE.md](BATCH_PROCESSING_GUIDE.md)
- Review system requirements: [SYSTEM_REQUIREMENTS.md](SYSTEM_REQUIREMENTS.md)
- Galaxy deployment: [GALAXY_DEPLOYMENT_GUIDE.md](GALAXY_DEPLOYMENT_GUIDE.md)
- Open issue on GitHub

## License

MIT License

## Citations

- YOLOv8: https://github.com/ultralytics/ultralytics
- RELION: doi:10.7554/eLife.18722
- CryoSPARC: doi:10.1038/nmeth.4169
