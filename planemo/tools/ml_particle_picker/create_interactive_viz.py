#!/usr/bin/env python3
"""
Create Interactive Visualization for CryoEM Particle Picking Results
Standalone tool that can be run after particle picking
"""

import argparse
import sys
import os
import numpy as np
import mrcfile
from pathlib import Path

# Add lib directory to path for validation imports
# Get the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up three levels to reach the project root, then into lib
lib_path = os.path.join(script_dir, '..', '..', '..', 'lib')
sys.path.insert(0, lib_path)

try:
    from validation import InputValidator, ErrorReporter
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False

def parse_star_file(star_file):
    """Parse RELION STAR file to extract coordinates and confidences."""
    coords = []
    confidences = []
    
    with open(star_file, 'r') as f:
        in_data = False
        for line in f:
            line = line.strip()
            if line.startswith('loop_'):
                in_data = True
                continue
            if in_data and line and not line.startswith('_'):
                parts = line.split()
                if len(parts) >= 3:
                    x = float(parts[0])
                    y = float(parts[1])
                    conf = float(parts[2])
                    coords.append([x, y])
                    confidences.append(conf)
    
    return np.array(coords), np.array(confidences)


def create_plotly_interactive(micrograph, coords, confidences, output_html, 
                              micrograph_name="micrograph"):
    """Create interactive Plotly visualization."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        print("ERROR: Plotly not installed. Install with: pip install plotly")
        return False
    
    # Downsample for web
    h, w = micrograph.shape
    max_size = 2048
    if max(h, w) > max_size:
        downsample = max(h, w) / max_size
        micrograph_display = micrograph[::int(downsample), ::int(downsample)]
        coords_display = coords / downsample
    else:
        micrograph_display = micrograph
        coords_display = coords
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Micrograph with Detected Particles', 
                       'Confidence Distribution', 
                       'Spatial Density Heatmap',
                       'Confidence vs X Position'),
        specs=[[{'type': 'image', 'rowspan': 2}, {'type': 'histogram'}],
               [None, {'type': 'scatter'}]],
        column_widths=[0.65, 0.35],
        row_heights=[0.5, 0.5]
    )
    
    # 1. Micrograph with particles
    fig.add_trace(
        go.Heatmap(
            z=micrograph_display,
            colorscale='gray',
            showscale=False,
            hoverinfo='skip'
        ),
        row=1, col=1
    )
    
    if len(coords_display) > 0:
        fig.add_trace(
            go.Scatter(
                x=coords_display[:, 0],
                y=coords_display[:, 1],
                mode='markers',
                marker=dict(
                    size=8,
                    color=confidences,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(
                        title="Confidence",
                        x=0.6,
                        len=0.9
                    ),
                    line=dict(width=1, color='white'),
                    cmin=0.3,
                    cmax=0.99
                ),
                text=[f'<b>Particle {i+1}</b><br>' +
                      f'Position: ({x:.0f}, {y:.0f})<br>' +
                      f'Confidence: {conf:.3f}'
                      for i, ((x, y), conf) in enumerate(zip(coords, confidences))],
                hovertemplate='%{text}<extra></extra>',
                name='Particles'
            ),
            row=1, col=1
        )
    
    # 2. Confidence histogram
    fig.add_trace(
        go.Histogram(
            x=confidences,
            nbinsx=25,
            marker_color='steelblue',
            marker_line_color='white',
            marker_line_width=1,
            name='Confidence',
            hovertemplate='Confidence: %{x:.3f}<br>Count: %{y}<extra></extra>'
        ),
        row=1, col=2
    )
    
    # 3. Confidence vs X position
    if len(coords) > 0:
        fig.add_trace(
            go.Scatter(
                x=coords[:, 0],
                y=confidences,
                mode='markers',
                marker=dict(
                    size=4,
                    color=confidences,
                    colorscale='Viridis',
                    showscale=False,
                    line=dict(width=0.5, color='white')
                ),
                text=[f'<b>Particle {i+1}</b><br>' +
                      f'X: {x:.0f}, Y: {y:.0f}<br>' +
                      f'Confidence: {conf:.3f}'
                      for i, ((x, y), conf) in enumerate(zip(coords, confidences))],
                hovertemplate='%{text}<extra></extra>',
                name='Confidence vs Position'
            ),
            row=2, col=2
        )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'<b>Interactive CryoEM Particle Picking Results</b><br>' +
                 f'<sub>{micrograph_name} | {len(coords)} particles detected | ' +
                 f'Mean confidence: {np.mean(confidences):.3f}</sub>',
            x=0.5,
            xanchor='center',
            font=dict(size=16)
        ),
        height=850,
        showlegend=False,
        hovermode='closest',
        template='plotly_white'
    )
    
    # Update axes
    fig.update_xaxes(title_text="X Position (pixels)", row=2, col=2)
    fig.update_yaxes(title_text="Confidence", row=2, col=2, range=[0.2, 1.0])
    fig.update_xaxes(title_text="Confidence", row=1, col=2)
    fig.update_yaxes(title_text="Count", row=1, col=2)
    fig.update_yaxes(autorange='reversed', row=1, col=1)
    
    # Save with interactive features
    fig.write_html(
        output_html,
        config={
            'toImageButtonOptions': {
                'format': 'png',
                'filename': f'{micrograph_name}_interactive',
                'height': 1200,
                'width': 1600,
                'scale': 2
            },
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'scrollZoom': True
        },
        include_plotlyjs='cdn'
    )
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Create interactive visualization for CryoEM particle picking results'
    )
    
    parser.add_argument('--micrograph', required=True, help='Input micrograph file (MRC/MRCS/ST)')
    parser.add_argument('--star_file', required=True, help='Input STAR file with coordinates')
    parser.add_argument('--output', required=True, help='Output HTML file')
    parser.add_argument('--name', default='micrograph', help='Micrograph name for display')
    
    args = parser.parse_args()
    
    try:
        print("🔬 Creating Interactive Visualization")
        print(f"Micrograph: {args.micrograph}")
        print(f"STAR file: {args.star_file}")
        
        # Validate inputs if validation is available
        if VALIDATION_AVAILABLE:
            print("\n📋 Validating inputs...")
            validator = InputValidator(args.micrograph, args.star_file)
            result = validator.validate_all()
            
            # Report validation results
            ErrorReporter.report_validation_results(result)
            
            # Exit if critical errors found
            if not result.is_valid:
                print("\n❌ Validation failed. Please fix the errors above and try again.", file=sys.stderr)
                return 1
            
            if result.has_warnings():
                print("\n⚠️  Validation completed with warnings. Processing will continue...\n")
        
        # Load micrograph
        print("📁 Loading micrograph...")
        try:
            with mrcfile.open(args.micrograph, mode='r', permissive=True) as mrc:
                data = mrc.data
                
                # Check if data was loaded successfully
                if data is None:
                    print(f"❌ ERROR: Failed to load micrograph data from {args.micrograph}")
                    print("   The file may be corrupted or in an unsupported format.")
                    return 1
                
                if len(data.shape) == 3:
                    # Tomogram - extract middle slice
                    micrograph = data[data.shape[0] // 2].copy()
                    print(f"   Extracted middle slice from tomogram")
                else:
                    micrograph = data.copy()
        except Exception as e:
            print(f"❌ ERROR: Failed to open micrograph file: {str(e)}")
            traceback.print_exc()
            return 1
        
        # Normalize
        micrograph = (micrograph - np.mean(micrograph)) / np.std(micrograph)
        print(f"   Micrograph shape: {micrograph.shape}")
        
        # Parse STAR file
        print("📊 Parsing STAR file...")
        coords, confidences = parse_star_file(args.star_file)
        print(f"   Found {len(coords)} particles")
        
        if len(coords) == 0:
            print("⚠️  No particles found in STAR file")
            return 1
        
        print(f"   Confidence range: {confidences.min():.3f} - {confidences.max():.3f}")
        print(f"   Mean confidence: {confidences.mean():.3f}")
        
        # Validate coordinates against micrograph dimensions
        if VALIDATION_AVAILABLE:
            coord_warnings = validator.validate_coordinates(coords, micrograph.shape)
            for warning in coord_warnings:
                print(warning, file=sys.stderr)
        
        # Create visualization
        print("🎨 Creating interactive visualization...")
        success = create_plotly_interactive(
            micrograph, coords, confidences, 
            args.output, args.name
        )
        
        if success:
            print(f"✅ Interactive visualization saved: {args.output}")
            print(f"   Open in web browser to explore!")
            return 0
        else:
            print("❌ Failed to create visualization")
            return 1
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
