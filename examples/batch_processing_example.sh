#!/bin/bash
# Example: Batch processing for large CryoEM datasets
# This script demonstrates how to process 1TB+ datasets efficiently

# Configuration
INPUT_DIR="/path/to/your/micrographs"  # Change this to your data directory
OUTPUT_DIR="/path/to/output/particles"  # Change this to your output directory
PARTICLE_SIZE=200                       # Adjust for your particle size
DEVICE="cuda"                           # Use "cpu" if no GPU available

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "CryoEM Batch Processing Example"
echo "=========================================="
echo "Input: $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo "Particle size: $PARTICLE_SIZE pixels"
echo "Device: $DEVICE"
echo "=========================================="

# Step 1: Test on first 10 files
echo ""
echo "Step 1: Testing on first 10 files..."
./run_batch_picker.sh \
    --input_dir "$INPUT_DIR" \
    --output_dir "${OUTPUT_DIR}/test" \
    --particle_size "$PARTICLE_SIZE" \
    --confidence_threshold 0.7 \
    --device "$DEVICE" \
    --max_files 10 \
    --summary_report "${OUTPUT_DIR}/test_summary.json" \
    --verbose

# Check test results
if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Test successful! Review results in ${OUTPUT_DIR}/test/"
    echo ""
    echo "Test summary:"
    cat "${OUTPUT_DIR}/test_summary.json" | python -m json.tool | grep -A 8 "summary"
else
    echo ""
    echo "✗ Test failed. Please check parameters and try again."
    exit 1
fi

# Step 2: Ask user to confirm full processing
echo ""
read -p "Proceed with full dataset processing? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Processing cancelled."
    exit 0
fi

# Step 3: Process full dataset
echo ""
echo "Step 2: Processing full dataset..."
./run_batch_picker.sh \
    --input_dir "$INPUT_DIR" \
    --output_dir "${OUTPUT_DIR}/particles" \
    --particle_size "$PARTICLE_SIZE" \
    --confidence_threshold 0.7 \
    --device "$DEVICE" \
    --recursive \
    --summary_report "${OUTPUT_DIR}/full_summary.json" \
    --log_file "${OUTPUT_DIR}/processing.log" \
    --verbose

# Check final results
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Batch processing complete!"
    echo "=========================================="
    echo ""
    echo "Results:"
    echo "  - STAR files: ${OUTPUT_DIR}/particles/"
    echo "  - Summary: ${OUTPUT_DIR}/full_summary.json"
    echo "  - Log: ${OUTPUT_DIR}/processing.log"
    echo ""
    echo "Summary statistics:"
    cat "${OUTPUT_DIR}/full_summary.json" | python -m json.tool | grep -A 8 "summary"
    echo ""
    echo "Next steps:"
    echo "  1. Review STAR files in ${OUTPUT_DIR}/particles/"
    echo "  2. Import to RELION or CryoSPARC for downstream processing"
    echo "  3. Check ${OUTPUT_DIR}/full_summary.json for detailed statistics"
else
    echo ""
    echo "✗ Processing failed. Check ${OUTPUT_DIR}/processing.log for details."
    exit 1
fi
