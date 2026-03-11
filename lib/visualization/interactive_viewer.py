#!/usr/bin/env python3
"""
Interactive Visualization for CryoEM Particle Picking Results
Uses Plotly for interactive plots and Bokeh for advanced interactions
"""

import numpy as np
from pathlib import Path
import json

def create_interactive_visualization(micrograph, coords, confidences, output_html, 
                                     particle_size=200, micrograph_name="micrograph"):
    """
    Create interactive HTML visualization using Plotly.
    
    Features:
    - Zoom and pan
    - Hover to see particle details
    - Click to highlight particles
    - Filter by confidence
    - Export coordinates
    """
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        from plotly.subplots import make_subplots
    except ImportError:
        print("⚠️  Plotly not installed. Install with: pip install plotly")
        return False
    
    # Downsample micrograph for web display
    h, w = micrograph.shape
    max_size = 2048
    if max(h, w) > max_size:
        downsample = max(h, w) / max_size
        micrograph_display = micrograph[::int(downsample), ::int(downsample)]
        coords_display = coords / downsample
    else:
        micrograph_display = micrograph
        coords_display = coords
    
    # Create figure with subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Micrograph with Particles', 'Confidence Distribution', 
                       'Particle Density Map', 'Confidence vs Position'),
        specs=[[{'type': 'image', 'rowspan': 2}, {'type': 'histogram'}],
               [None, {'type': 'scatter'}]],
        column_widths=[0.6, 0.4],
        row_heights=[0.5, 0.5]
    )
    
    # 1. Main micrograph with particles
    fig.add_trace(
        go.Heatmap(
            z=micrograph_display,
            colorscale='gray',
            showscale=False,
            hoverinfo='skip'
        ),
        row=1, col=1
    )
    
    # Add particles as scatter plot
    if len(coords_display) > 0:
        fig.add_trace(
            go.Scatter(
                x=coords_display[:, 0],
                y=coords_display[:, 1],
                mode='markers',
                marker=dict(
                    size=10,
                    color=confidences,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="Confidence", x=0.55),
                    line=dict(width=1, color='white')
                ),
                text=[f'Particle {i+1}<br>Confidence: {conf:.3f}<br>X: {x:.1f}, Y: {y:.1f}' 
                      for i, (conf, (x, y)) in enumerate(zip(confidences, coords))],
                hoverinfo='text',
                name='Particles'
            ),
            row=1, col=1
        )
    
    # 2. Confidence histogram
    fig.add_trace(
        go.Histogram(
            x=confidences,
            nbinsx=30,
            marker_color='steelblue',
            name='Confidence',
            hovertemplate='Confidence: %{x:.3f}<br>Count: %{y}<extra></extra>'
        ),
        row=1, col=2
    )
    
    # 3. Confidence vs Position scatter
    if len(coords) > 0:
        fig.add_trace(
            go.Scatter(
                x=coords[:, 0],
                y=confidences,
                mode='markers',
                marker=dict(
                    size=5,
                    color=confidences,
                    colorscale='Viridis',
                    showscale=False
                ),
                text=[f'Particle {i+1}<br>X: {x:.1f}, Y: {y:.1f}<br>Confidence: {conf:.3f}' 
                      for i, ((x, y), conf) in enumerate(zip(coords, confidences))],
                hoverinfo='text',
                name='Position vs Confidence'
            ),
            row=2, col=2
        )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'Interactive CryoEM Particle Picking Results<br><sub>{micrograph_name} - {len(coords)} particles detected</sub>',
            x=0.5,
            xanchor='center'
        ),
        height=800,
        showlegend=False,
        hovermode='closest'
    )
    
    # Update axes
    fig.update_xaxes(title_text="X Position (pixels)", row=2, col=2)
    fig.update_yaxes(title_text="Confidence", row=2, col=2)
    fig.update_xaxes(title_text="Confidence", row=1, col=2)
    fig.update_yaxes(title_text="Count", row=1, col=2)
    
    # Reverse y-axis for image (top-left origin)
    fig.update_yaxes(autorange='reversed', row=1, col=1)
    
    # Save to HTML
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
            'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape']
        }
    )
    
    print(f"✅ Interactive visualization saved: {output_html}")
    return True


def create_bokeh_visualization(micrograph, coords, confidences, output_html,
                               particle_size=200, micrograph_name="micrograph"):
    """
    Create advanced interactive visualization using Bokeh.
    
    Features:
    - Pan, zoom, box select
    - Lasso select particles
    - Linked brushing between plots
    - Real-time filtering
    - Data table with particle info
    """
    try:
        from bokeh.plotting import figure, output_file, save
        from bokeh.layouts import column, row
        from bokeh.models import HoverTool, ColumnDataSource, ColorBar, LinearColorMapper
        from bokeh.models.widgets import DataTable, TableColumn, Slider
        from bokeh.palettes import Viridis256
    except ImportError:
        print("⚠️  Bokeh not installed. Install with: pip install bokeh")
        return False
    
    output_file(output_html)
    
    # Downsample for display
    h, w = micrograph.shape
    max_size = 2048
    if max(h, w) > max_size:
        downsample = max(h, w) / max_size
        micrograph_display = micrograph[::int(downsample), ::int(downsample)]
        coords_display = coords / downsample
    else:
        micrograph_display = micrograph
        coords_display = coords
    
    # Prepare data
    source = ColumnDataSource(data=dict(
        x=coords_display[:, 0] if len(coords_display) > 0 else [],
        y=coords_display[:, 1] if len(coords_display) > 0 else [],
        confidence=confidences if len(confidences) > 0 else [],
        particle_id=[f'P{i+1}' for i in range(len(coords))] if len(coords) > 0 else []
    ))
    
    # Color mapper
    color_mapper = LinearColorMapper(palette=Viridis256, low=0.3, high=0.99)
    
    # Main micrograph plot
    p1 = figure(
        width=800, height=600,
        title=f"Micrograph: {micrograph_name}",
        tools="pan,wheel_zoom,box_zoom,reset,save,box_select,lasso_select"
    )
    
    # Show micrograph
    p1.image(image=[micrograph_display], x=0, y=0, dw=micrograph_display.shape[1], 
             dh=micrograph_display.shape[0], palette="Greys256")
    
    # Add particles
    if len(coords_display) > 0:
        particles = p1.circle(
            'x', 'y', source=source, size=10,
            fill_color={'field': 'confidence', 'transform': color_mapper},
            line_color='white', line_width=1,
            alpha=0.8, selection_color='red', nonselection_alpha=0.3
        )
        
        # Add hover tool
        hover = HoverTool(renderers=[particles], tooltips=[
            ("Particle", "@particle_id"),
            ("Position", "(@x{0.0}, @y{0.0})"),
            ("Confidence", "@confidence{0.000}")
        ])
        p1.add_tools(hover)
    
    # Confidence histogram
    p2 = figure(
        width=400, height=300,
        title="Confidence Distribution",
        tools="pan,wheel_zoom,reset,save"
    )
    
    if len(confidences) > 0:
        hist, edges = np.histogram(confidences, bins=30)
        p2.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
                fill_color="steelblue", line_color="white", alpha=0.7)
    
    p2.xaxis.axis_label = "Confidence"
    p2.yaxis.axis_label = "Count"
    
    # Scatter plot: Position vs Confidence
    p3 = figure(
        width=400, height=300,
        title="X Position vs Confidence",
        tools="pan,wheel_zoom,box_zoom,reset,save,box_select"
    )
    
    if len(coords) > 0:
        p3.circle('x', 'confidence', source=source, size=5,
                 fill_color={'field': 'confidence', 'transform': color_mapper},
                 line_color=None, alpha=0.6,
                 selection_color='red', nonselection_alpha=0.2)
    
    p3.xaxis.axis_label = "X Position"
    p3.yaxis.axis_label = "Confidence"
    
    # Layout
    layout = column(
        p1,
        row(p2, p3)
    )
    
    save(layout)
    print(f"✅ Bokeh visualization saved: {output_html}")
    return True


def create_3d_visualization(coords, confidences, output_html, micrograph_shape):
    """
    Create 3D visualization of particle distribution.
    Useful for understanding spatial patterns.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("⚠️  Plotly not installed")
        return False
    
    if len(coords) == 0:
        print("⚠️  No particles to visualize")
        return False
    
    # Create 3D scatter plot
    fig = go.Figure(data=[go.Scatter3d(
        x=coords[:, 0],
        y=coords[:, 1],
        z=confidences,
        mode='markers',
        marker=dict(
            size=5,
            color=confidences,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Confidence"),
            line=dict(width=0.5, color='white')
        ),
        text=[f'Particle {i+1}<br>X: {x:.1f}, Y: {y:.1f}<br>Confidence: {conf:.3f}' 
              for i, ((x, y), conf) in enumerate(zip(coords, confidences))],
        hoverinfo='text'
    )])
    
    fig.update_layout(
        title='3D Particle Distribution',
        scene=dict(
            xaxis_title='X Position',
            yaxis_title='Y Position',
            zaxis_title='Confidence',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        height=700
    )
    
    fig.write_html(output_html)
    print(f"✅ 3D visualization saved: {output_html}")
    return True


def export_interactive_data(coords, confidences, output_json, micrograph_name="micrograph"):
    """
    Export data in JSON format for custom visualizations.
    """
    data = {
        'micrograph': micrograph_name,
        'particle_count': len(coords),
        'particles': [
            {
                'id': i + 1,
                'x': float(x),
                'y': float(y),
                'confidence': float(conf)
            }
            for i, ((x, y), conf) in enumerate(zip(coords, confidences))
        ],
        'statistics': {
            'mean_confidence': float(np.mean(confidences)) if len(confidences) > 0 else 0,
            'std_confidence': float(np.std(confidences)) if len(confidences) > 0 else 0,
            'min_confidence': float(np.min(confidences)) if len(confidences) > 0 else 0,
            'max_confidence': float(np.max(confidences)) if len(confidences) > 0 else 0
        }
    }
    
    with open(output_json, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Interactive data exported: {output_json}")
    return True
