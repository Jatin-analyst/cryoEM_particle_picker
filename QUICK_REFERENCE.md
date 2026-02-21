# CryoEM Particle Picker - Quick Reference

## Installation

```bash
pip install -r requirements.txt
```

## Single File Processing

```bash
./run_picker.sh \
    --input micrograph.mrc \
    --output particles.star \
    --particle_size 200 \
    --device cpu
```

## Batch Processing (1TB+ Datasets)

```bash
./run_batch_picker.sh \
    --input_dir /path/to/micrographs \
    --output_dir /path/to/output \
    --particle_size 200 \
    --device cuda \
    --recursive \
    --summary_report report.json \
    --verbose
```

## Common Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--particle_size` | Particle diameter (pixels) | Required |
| `--confidence_threshold` | Detection threshold | 0.7 |
| `--device` | cpu or cuda | cpu |
| `--min_distance` | Min separation (pixels) | particle_size |
| `--edge_exclusion` | Edge buffer (pixels) | 0 |

## Batch-Specific Parameters

| Parameter | Description |
|-----------|-------------|
| `--recursive` | Search subdirectories |
| `--preserve_structure` | Maintain directory hierarchy |
| `--max_files` | Limit files (for testing) |
| `--summary_report` | JSON report path |

## Performance

| Hardware | Speed | 1000 Files |
|----------|-------|------------|
| CPU | ~1800/hour | ~33 min |
| GPU | ~7200/hour | ~8 min |

## File Formats

- ✅ `.mrc` - 2D micrographs
- ✅ `.mrcs` - MRC stacks
- ✅ `.st` - 3D tomograms (auto-extracts middle slice)

## Output

- **STAR files** - RELION/CryoSPARC compatible
- **JSON reports** - Batch processing statistics
- **Log files** - Detailed processing logs

## Documentation

- [BATCH_PROCESSING_GUIDE.md](BATCH_PROCESSING_GUIDE.md) - Batch processing
- [QUICKSTART.md](QUICKSTART.md) - Detailed quick start
- [SYSTEM_REQUIREMENTS.md](SYSTEM_REQUIREMENTS.md) - Performance specs
- [GALAXY_DEPLOYMENT_GUIDE.md](GALAXY_DEPLOYMENT_GUIDE.md) - Galaxy deployment

## Examples

### Test on 10 Files

```bash
./run_batch_picker.sh \
    --input_dir /data \
    --output_dir /test \
    --particle_size 200 \
    --max_files 10 \
    --verbose
```

### Process with CTF Estimation

```bash
./run_batch_picker.sh \
    --input_dir /data \
    --output_dir /output \
    --particle_size 200 \
    --ctf_estimation \
    --voltage 300 \
    --cs 2.7 \
    --pixel_size 1.0 \
    --device cuda
```

### High-Quality Processing

```bash
./run_batch_picker.sh \
    --input_dir /data \
    --output_dir /output \
    --particle_size 200 \
    --confidence_threshold 0.8 \
    --min_distance 250 \
    --edge_exclusion 100 \
    --device cuda
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No files found" | Check directory path and file extensions |
| "Out of memory" | Use `--device cpu` or reduce `--batch_size` |
| "Slow processing" | Use `--device cuda` for GPU acceleration |
| "No particles detected" | Lower `--confidence_threshold` to 0.5 |

## Help

```bash
# Single file help
./run_picker.sh --help

# Batch processing help
./run_batch_picker.sh --help
```

## Support

- GitHub Issues
- Documentation: [README.md](README.md)
- Batch Guide: [BATCH_PROCESSING_GUIDE.md](BATCH_PROCESSING_GUIDE.md)
