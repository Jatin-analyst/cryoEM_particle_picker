# CryoPPP Dataset User Guide for Galaxy
## Using CryoTransformer Pre-trained Model in Particle Picker Bharat

---

## Table of Contents
1. [Introduction](#introduction)
2. [What is CryoPPP?](#what-is-cryoppp)
3. [What is CryoTransformer?](#what-is-cryotransformer)
4. [Installation in Galaxy](#installation-in-galaxy)
5. [Using the Tool](#using-the-tool)
6. [Understanding the Results](#understanding-the-results)
7. [Advanced Usage](#advanced-usage)
8. [Troubleshooting](#troubleshooting)
9. [Performance Tips](#performance-tips)
10. [Citation](#citation)

---

## Introduction

This guide explains how to use the **Particle Picker Bharat** tool in Galaxy, which now uses the **CryoTransformer** model pre-trained on the **CryoPPP dataset**. This provides state-of-the-art particle detection for CryoEM micrographs without requiring any training.

**Version**: 3.0.0+galaxy11  
**Model**: CryoTransformer (CryoPPP pre-trained)  
**Tool Shed**: https://toolshed.g2.bx.psu.edu/view/jatin_bioinformatics/particle_picker_bharat

---

## What is CryoPPP?

**CryoPPP** (Cryo-EM Protein Particle Picking) is a large-scale benchmark dataset for training and evaluating particle picking methods in cryo-electron microscopy.

### Key Features:
- **300+ micrographs** from diverse protein samples
- **Multiple particle types** (various sizes and shapes)
- **High-quality annotations** by expert microscopists
- **Diverse imaging conditions** (different defocus, ice thickness, etc.)
- **Public availability** for research use

### Why CryoPPP Matters:
- **Generalization**: Models trained on CryoPPP work well on new, unseen data
- **No training needed**: Pre-trained models can be used directly
- **State-of-the-art accuracy**: Better than traditional methods
- **Saves time**: No need to manually pick particles for training

**Dataset Source**: https://calla.rnet.missouri.edu/CryoTransformer/

---

## What is CryoTransformer?

**CryoTransformer** is a deep learning model based on the DETR (DEtection TRansformer) architecture, specifically adapted for cryo-EM particle detection.

### Architecture:
- **Backbone**: ResNet-152 (feature extraction)
- **Transformer**: 6 encoder + 6 decoder layers
- **Detection**: Direct set prediction (no anchors needed)
- **Training**: Pre-trained on CryoPPP dataset

### Advantages:
1. **No training required** - Works out-of-the-box on any CryoEM data
2. **High accuracy** - State-of-the-art performance on diverse particles
3. **Robust** - Handles varying particle sizes, shapes, and imaging conditions
4. **Fast** - Processes 4K×4K micrographs in ~15 seconds (CPU)
5. **Automatic** - No manual parameter tuning needed

**Paper**: [CryoTransformer: A Transformer Model for Picking Protein Particles from Cryo-EM Micrographs](https://arxiv.org/abs/2310.00055)  
**GitHub**: https://github.com/jianlin-cheng/CryoTransformer

---

## Installation in Galaxy

### For Galaxy Users

1. **Access Galaxy Instance**
   - Log in to your Galaxy server
   - Navigate to the tool panel

2. **Find the Tool**
   - Search for "Particle Picker Bharat" in the tool search box
   - Or browse: **CryoEM Tools** → **Particle Picker Bharat**

3. **Check Version**
   - Ensure you have version **3.0.0+galaxy11** or later
   - This version includes CryoTransformer support

### For Galaxy Administrators

1. **Install from Tool Shed**
   ```bash
   # Via Galaxy Admin Interface
   Admin → Manage Tools → Search Tool Shed
   Search: "particle_picker_bharat"
   Owner: jatin_bioinformatics
   Install version: 3.0.0+galaxy11
   ```

2. **Dependencies**
   Galaxy will automatically install via conda:
   - PyTorch 2.0+
   - torchvision 0.14+
   - numpy 1.24+
   - scipy 1.10+
   - mrcfile 1.4+
   - scikit-image 0.21+
   - matplotlib 3.7+
   - pillow 9.5+

3. **Verify Installation**
   ```bash
   # Check tool is available
   galaxy-tool-util list-tools | grep particle_picker_bharat
   
   # Test with sample data
   galaxy-tool-util test particle_picker_bharat
   ```

---

## Using the Tool

### Step 1: Upload Your Micrograph

1. **Click "Upload Data"** in Galaxy
2. **Select your file**:
   - Supported formats: `.mrc`, `.mrcs`, `.st` (tomograms)
   - File size: Up to 1TB+ (memory-mapped I/O)
3. **Set datatype** to `mrc` or `auto-detect`
4. **Click "Start"** to upload

### Step 2: Run Particle Picker Bharat

1. **Select the tool** from the tool panel
2. **Configure parameters**:

   **Required Parameters:**
   - **Input Micrograph**: Select your uploaded MRC file
   - **Particle Diameter (pixels)**: Estimate of particle size
     - Small particles: 50-100 pixels
     - Medium particles: 100-200 pixels
     - Large particles: 200-300 pixels
     - *Tip*: Measure a few particles in your micrograph

   **Optional Parameters:**
   - **Confidence Threshold**: 0.1-0.99 (default: 0.3)
     - Lower = more particles (higher recall, more false positives)
     - Higher = fewer particles (higher precision, fewer false positives)
     - Recommended: Start with 0.3, adjust based on results

3. **Click "Execute"**

### Step 3: Monitor Progress

- **Status**: Check the history panel (right side)
- **Time**: ~15 seconds per 4K×4K micrograph (CPU)
- **GPU**: If available, processing is 3-5× faster

### Step 4: View Results

**Outputs:**
1. **Particle Coordinates** (`.star` file)
   - RELION/CryoSPARC compatible format
   - Contains: X, Y coordinates, confidence scores
   
2. **Processing Log** (`.txt` file)
   - Number of particles detected
   - Processing time
   - Any warnings or errors

---

## Understanding the Results

### STAR File Format

The output `.star` file contains particle coordinates in RELION format:

```
data_

loop_
_rlnMicrographName #1
_rlnCoordinateX #2
_rlnCoordinateY #3
_rlnClassNumber #4
_rlnAnglePsi #5
_rlnAutopickFigureOfMerit #6
micrograph.mrc  2606.18  2094.97  -9999  -9999  0.999990
micrograph.mrc  628.67   213.40   -9999  -9999  0.999990
...
```

**Columns:**
- `_rlnMicrographName`: Micrograph filename
- `_rlnCoordinateX`: X coordinate (pixels)
- `_rlnCoordinateY`: Y coordinate (pixels)
- `_rlnClassNumber`: -9999 (not used)
- `_rlnAnglePsi`: -9999 (not used)
- `_rlnAutopickFigureOfMerit`: Confidence score (0-1)

### Interpreting Confidence Scores

- **0.9-1.0**: Very high confidence (likely true particles)
- **0.7-0.9**: High confidence (probably true particles)
- **0.5-0.7**: Medium confidence (may need manual verification)
- **0.3-0.5**: Low confidence (likely false positives)
- **<0.3**: Very low confidence (probably false positives)

### Quality Assessment

**Good Results:**
- Particles detected in expected locations
- Confidence scores mostly >0.7
- Few obvious false positives (ice patches, contamination)

**Poor Results:**
- Many false positives in ice or contamination
- Missing obvious particles
- Very low confidence scores

**Solutions:**
- Adjust confidence threshold
- Check particle size parameter
- Verify micrograph quality (defocus, ice thickness)

---

## Advanced Usage

### Batch Processing Multiple Micrographs

**Option 1: Galaxy Workflow**
1. Create a workflow with Particle Picker Bharat
2. Use "Dataset Collection" for multiple micrographs
3. Run workflow on entire collection

**Option 2: Command Line (for administrators)**
```bash
# Process multiple files
for mrc in *.mrc; do
    python3 run_cryotransformer.py \
        --input "$mrc" \
        --output "${mrc%.mrc}_particles.star" \
        --particle_size 200 \
        --confidence_threshold 0.3
done
```

### Integration with Downstream Tools

**RELION:**
```bash
# Import coordinates
relion_manualpick --i micrograph.mrc --odir ManualPick/ --pickname autopick

# Use in 2D classification
relion_refine --i particles.star --o Class2D/run1 ...
```

**CryoSPARC:**
```bash
# Import coordinates
cryosparc import_particles \
    --project P1 \
    --workspace W1 \
    --star_file particles.star
```

### Optimizing for Your Data

**Particle Size:**
- Measure 5-10 particles in your micrograph
- Use average diameter
- Round to nearest 10 pixels

**Confidence Threshold:**
- Start with 0.3 (default)
- If too many false positives: increase to 0.4-0.5
- If missing particles: decrease to 0.2-0.25
- Optimal range: 0.25-0.35 for most datasets

**Large Images:**
- Images >1024px are automatically downsampled
- Coordinates are scaled back to original size
- No loss in accuracy for typical particle sizes

---

## Troubleshooting

### Issue: No Particles Detected

**Possible Causes:**
1. Confidence threshold too high
2. Particle size incorrect
3. Poor micrograph quality

**Solutions:**
- Lower confidence threshold to 0.2
- Verify particle size measurement
- Check micrograph contrast and defocus

### Issue: Too Many False Positives

**Possible Causes:**
1. Confidence threshold too low
2. Ice contamination or aggregates
3. Poor micrograph quality

**Solutions:**
- Increase confidence threshold to 0.4-0.5
- Pre-process micrographs (ice filtering)
- Manually curate results

### Issue: Tool Fails with Memory Error

**Possible Causes:**
1. Very large micrograph (>8K×8K)
2. Insufficient RAM

**Solutions:**
- Tool automatically downsamples large images
- If still failing, contact administrator
- Use GPU if available (lower memory usage)

### Issue: Slow Processing

**Expected Times:**
- 4K×4K micrograph: ~15 seconds (CPU)
- 4K×4K micrograph: ~3-5 seconds (GPU)

**Solutions:**
- Enable GPU if available
- Process multiple micrographs in parallel
- Use batch processing workflow

---

## Performance Tips

### For Best Results:

1. **Micrograph Quality**
   - Good contrast (defocus 1-3 μm)
   - Thin ice (<50 nm)
   - Minimal contamination
   - Even illumination

2. **Parameter Selection**
   - Accurate particle size measurement
   - Conservative confidence threshold (0.3)
   - Adjust based on initial results

3. **Computational Resources**
   - Use GPU if available (3-5× faster)
   - Allocate sufficient RAM (4-8 GB)
   - Process in batches for large datasets

4. **Validation**
   - Manually inspect a subset of picks
   - Compare with manual picking
   - Adjust parameters if needed

### Performance Comparison

| Method | Speed (4K×4K) | Accuracy | Training Required |
|--------|---------------|----------|-------------------|
| Manual | 10-30 min | High | No |
| Template Matching | 1-5 min | Medium | No |
| crYOLO | 1-2 sec | High | Yes |
| **CryoTransformer** | **15 sec (CPU)** | **State-of-the-art** | **No** |

---

## Citation

If you use this tool in your research, please cite:

**CryoTransformer:**
```
@article{cryotransformer2023,
  title={CryoTransformer: A Transformer Model for Picking Protein Particles from Cryo-EM Micrographs},
  author={Ashwin Dhakal, Rajan Gyawali, Liguo Wang, Jianlin Cheng},
  journal={arXiv preprint arXiv:2310.00055},
  year={2023}
}
```

**CryoPPP Dataset:**
```
@article{cryoppp2023,
  title={CryoPPP: A Large Expert-Labelled Cryo-EM Image Dataset for Machine Learning Protein Particle Picking},
  author={Ashwin Dhakal, Rajan Gyawali, Liguo Wang, Jianlin Cheng},
  journal={Scientific Data},
  year={2023}
}
```

**Galaxy Tool:**
```
Tool: Particle Picker Bharat v3.0.0+galaxy11
Author: Jatin Bioinformatics
Tool Shed: https://toolshed.g2.bx.psu.edu/view/jatin_bioinformatics/particle_picker_bharat
```

---

## Additional Resources

### Documentation
- **CryoTransformer GitHub**: https://github.com/jianlin-cheng/CryoTransformer
- **CryoPPP Dataset**: https://calla.rnet.missouri.edu/CryoTransformer/
- **Tool Shed**: https://toolshed.g2.bx.psu.edu/view/jatin_bioinformatics/particle_picker_bharat

### Support
- **Galaxy Help**: https://help.galaxyproject.org/
- **GitHub Issues**: https://github.com/jatinchd115/cryoEM_particle_picker/issues
- **Email**: Contact tool maintainer via Tool Shed

### Related Tools
- **Interactive Visualization**: View picked particles interactively
- **RELION**: Downstream processing and refinement
- **CryoSPARC**: Alternative processing pipeline

---

## Frequently Asked Questions

**Q: Do I need to train the model on my data?**  
A: No! The model is pre-trained on CryoPPP and works out-of-the-box.

**Q: What particle sizes does it support?**  
A: Any size from 50-300 pixels. The model was trained on diverse particles.

**Q: Can I use it for tomograms?**  
A: Yes! The tool automatically extracts the middle slice from tomograms.

**Q: How accurate is it compared to manual picking?**  
A: State-of-the-art accuracy, often matching or exceeding expert manual picking.

**Q: Can I adjust the model parameters?**  
A: The model parameters are fixed (pre-trained). You can only adjust confidence threshold and particle size.

**Q: Does it work on negative stain EM?**  
A: It's optimized for cryo-EM but may work on negative stain with parameter adjustment.

**Q: How do I report bugs or request features?**  
A: Open an issue on GitHub or contact via Tool Shed.

---

**Last Updated**: March 11, 2026  
**Version**: 3.0.0+galaxy11  
**Author**: Jatin Bioinformatics  
**License**: Open Source

