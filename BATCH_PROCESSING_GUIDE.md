# Batch Processing Guide - CryoEM Particle Picker

## Overview

The batch processing feature allows you to process **1TB+ datasets** containing thousands of micrographs efficiently. Instead of running the tool once per file, you can process entire directories with a single command.

## Key Features

✅ **Directory-based processing** - Process all micrographs in a folder  
✅ **Recursive search** - Optionally search subdirectories  
✅ **Error resilience** - Failures don't stop the batch  
✅ **Progress tracking** - Real-time progress updates  
✅ **Summary reports** - JSON reports with detailed statistics  
✅ **Preserve structure** - Optionally maintain directory hierarchy in output  
✅ **Memory efficient** - Processes one file at a time (safe for large datasets)  

## Quick Start

### Basic Usage

```bash
./run_batch_picker.sh \
    --input_dir /path/to/micrographs \
    --output_dir /path/to/output \
    --particle_size 200 \
    --device cpu
```

### With All Options

```bash
./run_batch_picker.sh \
    --input_dir /path/to/micrographs \
    --output_dir /path/to/output \
    --particle_size 200 \
    --confidence_threshold 0.7 \
    --device cuda \
    --recursive \
    --preserve_structure \
    --summary_report batch_report.json \
    --verbose
```

## Command-Line Options

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--input_dir` | Directory containing micrographs | `/data/cryoem/session1` |
| `--output_dir` | Directory for output STAR files | `/data/output/particles` |
| `--particle_size` | Particle diameter in pixels | `200` |

### Model Parameters

| Argument | Description | Default |
|----------|-------------|---------|
| `--model_path` | Custom model weights path | Pretrained YOLOv8n |
| `--confidence_threshold` | Detection threshold (0.1-0.99) | `0.7` |
| `--device` | cpu or cuda | `cpu` |
| `--batch_size` | Inference batch size | `128` |

### Batch Processing Options

| Argument | Description | Default |
|----------|-------------|---------|
| `--recursive` | Search subdirectories | Off |
| `--preserve_structure` | Maintain directory structure in output | Off |
| `--max_files` | Limit number of files (for testing) | None (all files) |

### Post-Processing Options

| Argument | Description | Default |
|----------|-------------|---------|
| `--min_distance` | Min distance between particles (pixels) | `particle_size` |
| `--edge_exclusion` | Exclude particles near edges (pixels) | `0` |

### CTF Estimation

| Argument | Description | Default |
|----------|-------------|---------|
| `--ctf_estimation` | Enable CTF estimation | Off |
| `--voltage` | Acceleration voltage (kV) | `300.0` |
| `--cs` | Spherical aberration (mm) | `2.7` |
| `--pixel_size` | Pixel size (Å/pixel) | `1.0` |

### Output Options

| Argument | Description | Default |
|----------|-------------|---------|
| `--summary_report` | Path for JSON summary report | None |
| `--verbose` | Detailed progress output | Off |
| `--log_file` | Log file path | None |

## Usage Examples

### Example 1: Process Single Directory (Flat Structure)

```bash
# Process all .mrc, .mrcs, .st files in one directory
./run_batch_picker.sh \
    --input_dir /data/micrographs \
    --output_dir /data/particles \
    --particle_size 200 \
    --device cpu \
    --verbose
```

**Input:**
```
/data/micrographs/
├── mic_001.mrc
├── mic_002.mrc
└── mic_003.st
```

**Output:**
```
/data/particles/
├── mic_001_particles.star
├── mic_002_particles.star
└── mic_003_particles.star
```

### Example 2: Process Directory Tree (Recursive)

```bash
# Process all files including subdirectories
./run_batch_picker.sh \
    --input_dir /data/session1 \
    --output_dir /data/output \
    --particle_size 200 \
    --recursive \
    --preserve_structure \
    --device cuda \
    --verbose
```

**Input:**
```
/data/session1/
├── grid1/
│   ├── mic_001.mrc
│   └── mic_002.mrc
└── grid2/
    ├── mic_003.mrc
    └── mic_004.mrc
```

**Output (with --preserve_structure):**
```
/data/output/
├── grid1/
│   ├── mic_001_particles.star
│   └── mic_002_particles.star
└── grid2/
    ├── mic_003_particles.star
    └── mic_004_particles.star
```

### Example 3: Large Dataset with Summary Report

```bash
# Process 1TB+ dataset with progress tracking
./run_batch_picker.sh \
    --input_dir /mnt/storage/cryoem_data \
    --output_dir /mnt/output/particles \
    --particle_size 200 \
    --confidence_threshold 0.7 \
    --device cuda \
    --recursive \
    --summary_report /mnt/output/batch_summary.json \
    --log_file /mnt/output/batch_processing.log \
    --verbose
```

### Example 4: Test Run (Limited Files)

```bash
# Test on first 10 files before processing full dataset
./run_batch_picker.sh \
    --input_dir /data/large_dataset \
    --output_dir /data/test_output \
    --particle_size 200 \
    --max_files 10 \
    --device cpu \
    --verbose
```

### Example 5: High-Quality Processing with CTF

```bash
# Full pipeline with CTF estimation
./run_batch_picker.sh \
    --input_dir /data/micrographs \
    --output_dir /data/particles \
    --particle_size 200 \
    --confidence_threshold 0.8 \
    --min_distance 250 \
    --edge_exclusion 100 \
    --ctf_estimation \
    --voltage 300 \
    --cs 2.7 \
    --pixel_size 1.0 \
    --device cuda \
    --summary_report batch_report.json \
    --verbose
```

## Summary Report Format

The JSON summary report contains:

```json
{
  "summary": {
    "total_files": 1000,
    "successful": 998,
    "failed": 2,
    "success_rate": 99.8,
    "total_particles": 125000,
    "average_particles_per_file": 125.25,
    "total_time": 3600.5,
    "average_time_per_file": 3.6
  },
  "results": [
    {
      "filename": "mic_001.mrc",
      "success": true,
      "particles_detected": 125,
      "processing_time": 3.5,
      "error_message": null
    },
    {
      "filename": "mic_002.mrc",
      "success": false,
      "particles_detected": 0,
      "processing_time": 0.1,
      "error_message": "File corrupted"
    }
  ]
}
```

## Performance Expectations

### Processing Speed

| Hardware | Files/Hour | Time for 1000 Files |
|----------|------------|---------------------|
| CPU (4 cores) | ~1800 files/hour | ~33 minutes |
| GPU (NVIDIA) | ~7200 files/hour | ~8 minutes |

### Memory Usage

- **Per file**: ~200-500 MB (depending on image size)
- **Total**: Constant (processes one file at a time)
- **Safe for**: 1TB+ datasets on systems with 4GB+ RAM

### Disk Space

For 1TB of input micrographs:
- **STAR files**: ~10-50 MB (text files are small)
- **Summary report**: ~1-10 MB (depending on number of files)

## Handling Large Datasets (1TB+)

### Best Practices

1. **Use GPU if available** - 4x faster than CPU
2. **Test first** - Use `--max_files 10` to test parameters
3. **Enable logging** - Use `--log_file` to track progress
4. **Generate reports** - Use `--summary_report` for statistics
5. **Monitor disk space** - Ensure output directory has sufficient space
6. **Use recursive mode** - Process entire directory trees efficiently

### Example Workflow for 1TB Dataset

```bash
# Step 1: Test on 10 files
./run_batch_picker.sh \
    --input_dir /mnt/storage/cryoem_1tb \
    --output_dir /mnt/output/test \
    --particle_size 200 \
    --max_files 10 \
    --device cuda \
    --verbose

# Step 2: Review test results
cat /mnt/output/test/*.star

# Step 3: Process full dataset
./run_batch_picker.sh \
    --input_dir /mnt/storage/cryoem_1tb \
    --output_dir /mnt/output/particles \
    --particle_size 200 \
    --confidence_threshold 0.7 \
    --device cuda \
    --recursive \
    --summary_report /mnt/output/summary.json \
    --log_file /mnt/output/processing.log \
    --verbose

# Step 4: Check summary
cat /mnt/output/summary.json
```

## Error Handling

### Resilient Processing

The batch processor continues even if individual files fail:

```
[1/1000] mic_001.mrc
  ✓ Success: 125 particles in 3.5s
[2/1000] mic_002.mrc
  ✗ Failed: File corrupted
[3/1000] mic_003.mrc
  ✓ Success: 130 particles in 3.6s
...
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "File corrupted" | Damaged MRC file | Skip or re-acquire |
| "Out of memory" | Image too large | Reduce batch_size or use CPU |
| "No particles detected" | Low confidence threshold | Lower threshold or check data |
| "Permission denied" | File access issue | Check file permissions |

## Monitoring Progress

### Real-Time Monitoring

```bash
# Watch log file in real-time
tail -f /mnt/output/processing.log

# Check progress
grep "Success" /mnt/output/processing.log | wc -l
```

### Estimating Completion Time

```bash
# After processing some files, check average time
# Example: 100 files in 300 seconds = 3s/file
# Remaining: 900 files × 3s = 2700s = 45 minutes
```

## Integration with Pipelines

### Shell Script Integration

```bash
#!/bin/bash
# Process multiple sessions

for session in /data/sessions/*/; do
    echo "Processing session: $session"
    
    ./run_batch_picker.sh \
        --input_dir "$session" \
        --output_dir "/data/output/$(basename $session)" \
        --particle_size 200 \
        --device cuda \
        --recursive \
        --summary_report "/data/output/$(basename $session)_summary.json"
done
```

### Python Integration

```python
import subprocess
import json

# Run batch processing
result = subprocess.run([
    './run_batch_picker.sh',
    '--input_dir', '/data/micrographs',
    '--output_dir', '/data/particles',
    '--particle_size', '200',
    '--summary_report', 'summary.json'
], capture_output=True)

# Load summary
with open('summary.json') as f:
    summary = json.load(f)

print(f"Processed {summary['summary']['total_files']} files")
print(f"Success rate: {summary['summary']['success_rate']}%")
```

## Troubleshooting

### Issue: "No micrograph files found"

**Cause**: Input directory is empty or contains unsupported formats

**Solution**:
```bash
# Check directory contents
ls -lh /path/to/input_dir

# Verify file extensions (.mrc, .mrcs, .st)
```

### Issue: "Out of memory"

**Cause**: GPU memory exhausted

**Solution**:
```bash
# Use CPU mode
--device cpu

# Or reduce batch size
--batch_size 32
```

### Issue: "Processing is slow"

**Cause**: Using CPU instead of GPU

**Solution**:
```bash
# Check if GPU is available
nvidia-smi

# Use GPU mode
--device cuda
```

### Issue: "Many files failing"

**Cause**: Incorrect particle size or threshold

**Solution**:
```bash
# Test with different parameters
./run_batch_picker.sh \
    --input_dir /data/test \
    --output_dir /data/test_output \
    --particle_size 150 \
    --confidence_threshold 0.5 \
    --max_files 5 \
    --verbose
```

## Comparison: Single vs Batch Processing

| Feature | Single File | Batch Processing |
|---------|-------------|------------------|
| Command | `./run_picker.sh` | `./run_batch_picker.sh` |
| Input | One file | Directory of files |
| Output | One STAR file | Multiple STAR files |
| Error handling | Stops on error | Continues on error |
| Progress tracking | Single file | All files |
| Summary report | No | Yes (JSON) |
| Best for | Testing, single files | Production, large datasets |

## Next Steps

1. **Test on small dataset** - Verify parameters work correctly
2. **Review test results** - Check STAR files and summary report
3. **Process full dataset** - Run on complete 1TB+ dataset
4. **Import to RELION/CryoSPARC** - Use STAR files for downstream processing

## Support

For issues or questions:
- Check troubleshooting section above
- Review log files for detailed error messages
- Check summary report for failed files
- Open issue on GitHub

---

**Ready to process 1TB+ datasets efficiently!** 🚀
