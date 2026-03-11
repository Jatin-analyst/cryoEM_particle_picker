# Interactive Visualization for CryoEM Particle Picking

## Overview

The **Interactive Particle Visualization** tool creates web-based, interactive visualizations of particle picking results using Plotly. Unlike static PNG images, these visualizations allow you to zoom, pan, hover, and explore your data dynamically.

---

## Features

### 🎨 Interactive Elements

1. **Zoom and Pan**
   - Scroll to zoom in/out
   - Click and drag to pan
   - Double-click to reset view
   - Box zoom for precise regions

2. **Hover Information**
   - Particle ID
   - X, Y coordinates
   - Confidence score
   - Real-time updates

3. **Multiple Views**
   - Main micrograph with particles
   - Confidence histogram
   - Spatial distribution plot
   - Linked interactions

4. **Export Options**
   - Save as high-resolution PNG
   - Download plot data
   - Share HTML file

---

## Comparison with Other Tools

### vs Phyloseq (Microbiome Visualization)

While phyloseq is excellent for microbiome data, our tool is specifically designed for CryoEM:

| Feature | Phyloseq | Our Tool |
|---------|----------|----------|
| **Data Type** | Microbiome (OTU tables) | CryoEM (particle coordinates) |
| **Visualization** | Ordination, heatmaps | Spatial, confidence plots |
| **Interactivity** | ggplotly integration | Native Plotly |
| **Use Case** | Taxonomic analysis | Particle quality control |
| **Input Format** | phyloseq object | STAR files + micrographs |

### vs Other CryoEM Tools

| Tool | Interactivity | Features | Installation |
|------|--------------|----------|--------------|
| **Our Tool** | ✅ Full | Zoom, hover, export | Simple (pip) |
| **RELION Display** | ❌ Static | Basic overlay | Included |
| **CryoSPARC** | ⚠️ Limited | Web interface | Complex |
| **EMAN2** | ❌ Static | Manual inspection | Moderate |
| **Scipion** | ⚠️ Limited | Protocol viewer | Complex |

---

## Installation

### Prerequisites

```bash
# Install Plotly (required)
pip install plotly

# Optional: Install Bokeh for advanced features
pip install bokeh
```

### For Galaxy

```bash
# Standard Galaxy
pip install plotly

# Docker Galaxy
docker exec YOUR_CONTAINER bash -c \
  "source /galaxy_venv/bin/activate && pip install plotly"
```

---

## Usage

### Method 1: Galaxy Tool (Recommended)

1. **Run Particle Picker Bharat**
   - Process your micrograph
   - Get STAR file output

2. **Run Interactive Visualization Tool**
   - Input: Original micrograph
   - Input: STAR file from step 1
   - Output: HTML file

3. **View Results**
   - Download HTML file
   - Open in web browser
   - Explore interactively!

### Method 2: Command Line

```bash
python3 create_interactive_viz.py \
  --micrograph my_micrograph.mrc \
  --star_file particles.star \
  --output interactive_viz.html \
  --name "My Experiment"
```

### Method 3: Python Script

```python
from visualization.interactive_viewer import create_interactive_visualization
import mrcfile
import numpy as np

# Load data
with mrcfile.open('micrograph.mrc') as mrc:
    micrograph = mrc.data

coords = np.array([[100, 200], [300, 400]])  # Your coordinates
confidences = np.array([0.85, 0.92])  # Your confidences

# Create visualization
create_interactive_visualization(
    micrograph, coords, confidences,
    'output.html',
    particle_size=200,
    micrograph_name='My Sample'
)
```

---

## Visualization Types

### 1. Plotly Interactive (Default)

**Best for**: General use, presentations, sharing

**Features**:
- Fast loading
- Smooth interactions
- Easy sharing
- CDN-based (requires internet)

**Output**: Single HTML file (~1-5 MB)

### 2. Bokeh Advanced (Optional)

**Best for**: Advanced analysis, linked brushing

**Features**:
- Lasso selection
- Linked plots
- Data tables
- Real-time filtering

**Output**: HTML with embedded JavaScript

### 3. 3D Visualization (Optional)

**Best for**: Spatial pattern analysis

**Features**:
- 3D scatter plot
- Rotate and zoom
- Confidence as Z-axis
- Pattern detection

**Output**: Interactive 3D HTML

---

## Use Cases

### 1. Quality Control

**Scenario**: Verify particle picking quality

**Workflow**:
```
1. Run particle picker
2. Create interactive visualization
3. Zoom in on suspicious regions
4. Hover to check confidence scores
5. Identify false positives
6. Adjust parameters and re-run
```

### 2. Parameter Optimization

**Scenario**: Find optimal confidence threshold

**Workflow**:
```
1. Run picker with confidence 0.3
2. Create visualization
3. Examine confidence histogram
4. Identify natural threshold
5. Re-run with optimized threshold
```

### 3. Presentation and Publication

**Scenario**: Create figures for talks/papers

**Workflow**:
```
1. Create interactive visualization
2. Zoom to interesting region
3. Export high-resolution PNG
4. Include in presentation
5. Share HTML for interactive version
```

### 4. Collaboration

**Scenario**: Share results with team

**Workflow**:
```
1. Create visualization
2. Send HTML file via email
3. Team members open in browser
4. Discuss specific particles
5. Make decisions collaboratively
```

### 5. Training and Education

**Scenario**: Teach particle picking concepts

**Workflow**:
```
1. Create visualizations of good/bad picks
2. Students explore interactively
3. Hover to see confidence scores
4. Learn to identify quality particles
5. Practice parameter selection
```

---

## Advanced Features

### Custom Color Schemes

```python
# Use different colorscale
create_interactive_visualization(
    micrograph, coords, confidences,
    'output.html',
    colorscale='Plasma'  # or 'Viridis', 'Cividis', 'Turbo'
)
```

### Filter by Confidence

```python
# Show only high-confidence particles
mask = confidences > 0.7
filtered_coords = coords[mask]
filtered_conf = confidences[mask]

create_interactive_visualization(
    micrograph, filtered_coords, filtered_conf,
    'high_confidence.html'
)
```

### Export Data for Custom Analysis

```python
from visualization.interactive_viewer import export_interactive_data

# Export to JSON
export_interactive_data(
    coords, confidences,
    'particles.json',
    micrograph_name='Sample1'
)

# Use in custom JavaScript visualization
# Or import into other tools
```

---

## Performance Considerations

### File Size

| Particles | HTML Size | Load Time |
|-----------|-----------|-----------|
| < 100 | < 1 MB | Instant |
| 100-1000 | 1-3 MB | < 1 second |
| 1000-10000 | 3-10 MB | 1-3 seconds |
| > 10000 | > 10 MB | 3-10 seconds |

### Optimization Tips

1. **Downsample micrograph**: Automatically done for display
2. **Filter particles**: Show only high-confidence
3. **Use CDN**: Faster loading with internet
4. **Modern browser**: Chrome/Firefox recommended

---

## Troubleshooting

### Issue: Visualization doesn't load

**Causes**:
- No internet connection (Plotly CDN)
- Browser compatibility
- File corruption

**Solutions**:
```bash
# Use offline mode
pip install plotly-orca

# Or use local Plotly
# Modify script to use include_plotlyjs='directory'
```

### Issue: Slow performance

**Causes**:
- Too many particles (>10,000)
- Large micrograph
- Old browser

**Solutions**:
- Filter by confidence
- Downsample micrograph
- Use modern browser
- Close other tabs

### Issue: Particles not visible

**Causes**:
- Coordinates outside bounds
- Wrong file format
- Empty STAR file

**Solutions**:
- Check STAR file format
- Verify coordinates
- Check for parsing errors

---

## Examples

### Example 1: Basic Visualization

```bash
python3 create_interactive_viz.py \
  --micrograph sample.mrc \
  --star_file particles.star \
  --output viz.html
```

### Example 2: Batch Processing

```bash
# Create visualizations for all results
for mrc in *.mrc; do
    base=$(basename $mrc .mrc)
    python3 create_interactive_viz.py \
      --micrograph $mrc \
      --star_file ${base}.star \
      --output ${base}_interactive.html \
      --name $base
done
```

### Example 3: Galaxy Workflow

```
Input: Dataset Collection (Micrographs)
  ↓
Particle Picker Bharat (Batch)
  ↓
Interactive Visualization (Batch)
  ↓
Output: Collection of HTML files
```

---

## Future Enhancements

### Planned Features

1. **Real-time filtering**: Slider to adjust confidence threshold
2. **Particle selection**: Click to select/deselect particles
3. **Export selected**: Save filtered STAR file
4. **Comparison mode**: Compare multiple picking runs
5. **Annotation tools**: Draw regions of interest
6. **Statistics panel**: Live statistics updates

### Integration Plans

1. **RELION integration**: Direct import from RELION
2. **CryoSPARC integration**: Import from CryoSPARC
3. **Napari plugin**: 3D visualization in Napari
4. **Jupyter widgets**: Interactive notebooks
5. **Web service**: Online visualization tool

---

## Comparison Summary

### Why Not Phyloseq?

Phyloseq is excellent for its domain (microbiome), but:
- ❌ Not designed for spatial data
- ❌ No image overlay capabilities
- ❌ Different data structures
- ❌ Focused on taxonomic analysis

### Why Our Tool?

- ✅ Purpose-built for CryoEM
- ✅ Spatial visualization
- ✅ Image overlay
- ✅ Confidence scoring
- ✅ STAR file compatible
- ✅ Galaxy integrated

---

## Conclusion

Interactive visualization transforms particle picking from a black-box process into an explorable, understandable workflow. By providing zoom, hover, and export capabilities, researchers can:

- Validate results with confidence
- Optimize parameters intelligently
- Share findings effectively
- Teach concepts clearly
- Collaborate seamlessly

**Get Started**: Install Plotly and try the interactive visualization tool today!

---

**Version**: 1.0.0  
**Last Updated**: March 2026  
**Dependencies**: plotly, numpy, mrcfile  
**License**: Open Source
