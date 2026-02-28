"""
File I/O utilities for CryoEM Precision Tool
STAR file writing, advanced visualization, and statistics plotting
"""

import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

# Handle imports for both package and direct execution
try:
    from ..data_models import CTFParameters
    from ..visualization import ParticleVisualizationSuite
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from data_models import CTFParameters
    from visualization import ParticleVisualizationSuite


def write_star_file(
    filepath: str,
    coords: np.ndarray,
    confidences: np.ndarray,
    ctf_params: Optional[CTFParameters] = None,
    micrograph_name: str = ""
) -> None:
    """
    Write STAR file in RELION/CryoSPARC format.
    
    Args:
        filepath: Output file path
        coords: Particle coordinates (N, 2) as [x, y]
        confidences: Confidence scores (N,)
        ctf_params: Optional CTF parameters
        micrograph_name: Name of source micrograph
    """
    with open(filepath, 'w') as f:
        # Write header
        f.write("data_\n\n")
        f.write("loop_\n")
        f.write("_rlnCoordinateX\n")
        f.write("_rlnCoordinateY\n")
        f.write("_rlnAutopickFigureOfMerit\n")
        
        # Add CTF columns if available
        if ctf_params is not None:
            f.write("_rlnDefocusU\n")
            f.write("_rlnDefocusV\n")
            f.write("_rlnDefocusAngle\n")
            f.write("_rlnCtfAstigmatism\n")
            f.write("_rlnCtfMaxResolution\n")
            f.write("_rlnCtfFigureOfMerit\n")
        
        # Write particle data
        for i in range(len(coords)):
            x, y = coords[i]
            conf = confidences[i]
            
            if ctf_params is not None:
                # Include CTF parameters
                f.write(f"{x:.2f}  {y:.2f}  {conf:.4f}  ")
                f.write(f"{ctf_params.defocus_u:.4f}  ")
                f.write(f"{ctf_params.defocus_v:.4f}  ")
                f.write(f"{ctf_params.astigmatism_angle:.2f}  ")
                f.write(f"{ctf_params.astigmatism:.2f}  ")
                f.write(f"{ctf_params.max_resolution:.2f}  ")
                f.write(f"{ctf_params.fit_quality:.4f}\n")
            else:
                # Coordinates and confidence only
                f.write(f"{x:.2f}  {y:.2f}  {conf:.4f}\n")


def write_confidence_map(
    filepath: str,
    image_shape: Tuple[int, int],
    coords: np.ndarray,
    confidences: np.ndarray,
    use_plotly: bool = True
) -> None:
    """
    Generate confidence heatmap visualization.
    
    Args:
        filepath: Output PNG file path
        image_shape: Shape of original micrograph (H, W)
        coords: Particle coordinates (N, 2) as [x, y]
        confidences: Confidence scores (N,)
        use_plotly: Use Plotly (True) or Matplotlib/Seaborn (False)
    """
    if use_plotly:
        _write_confidence_map_plotly(filepath, image_shape, coords, confidences)
    else:
        _write_confidence_map_matplotlib(filepath, image_shape, coords, confidences)


def _write_confidence_map_plotly(
    filepath: str,
    image_shape: Tuple[int, int],
    coords: np.ndarray,
    confidences: np.ndarray
) -> None:
    """Generate confidence heatmap using Plotly."""
    try:
        import plotly.graph_objects as go
        import plotly.io as pio
        
        h, w = image_shape
        
        # Create scatter plot
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=coords[:, 0],
            y=coords[:, 1],
            mode='markers',
            marker=dict(
                size=8,
                color=confidences,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Confidence"),
                line=dict(width=0.5, color='white')
            ),
            text=[f"Conf: {c:.3f}" for c in confidences],
            hovertemplate='X: %{x}<br>Y: %{y}<br>%{text}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title="Particle Detection Confidence Map",
            xaxis=dict(title="X (pixels)", range=[0, w]),
            yaxis=dict(title="Y (pixels)", range=[h, 0]),  # Invert Y axis
            width=800,
            height=int(800 * h / w),
            hovermode='closest'
        )
        
        # Save as PNG
        pio.write_image(fig, filepath, format='png')
        
    except ImportError:
        # Fallback to matplotlib if plotly not available
        _write_confidence_map_matplotlib(filepath, image_shape, coords, confidences)


def _write_confidence_map_matplotlib(
    filepath: str,
    image_shape: Tuple[int, int],
    coords: np.ndarray,
    confidences: np.ndarray
) -> None:
    """Generate confidence heatmap using Matplotlib/Seaborn."""
    h, w = image_shape
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 10 * h / w))
    
    # Create scatter plot
    scatter = ax.scatter(
        coords[:, 0],
        coords[:, 1],
        c=confidences,
        cmap='viridis',
        s=50,
        alpha=0.7,
        edgecolors='white',
        linewidth=0.5
    )
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Confidence Score', rotation=270, labelpad=20)
    
    # Set labels and title
    ax.set_xlabel('X (pixels)')
    ax.set_ylabel('Y (pixels)')
    ax.set_title('Particle Detection Confidence Map')
    
    # Set axis limits
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)  # Invert Y axis
    
    # Save figure
    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()


def generate_statistics_plot(
    coords: np.ndarray,
    confidences: np.ndarray,
    output_path: str
) -> None:
    """
    Generate statistical visualization using Seaborn.
    
    Creates a figure with:
    - Confidence score distribution histogram
    - Spatial distribution scatter plot
    
    Args:
        coords: Particle coordinates (N, 2) as [x, y]
        confidences: Confidence scores (N,)
        output_path: Output file path
    """
    # Set seaborn style
    sns.set_style("whitegrid")
    
    # Create figure with subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Confidence distribution
    ax1 = axes[0]
    sns.histplot(confidences, bins=30, kde=True, ax=ax1, color='steelblue')
    ax1.set_xlabel('Confidence Score')
    ax1.set_ylabel('Count')
    ax1.set_title('Confidence Score Distribution')
    ax1.axvline(np.mean(confidences), color='red', linestyle='--', 
                label=f'Mean: {np.mean(confidences):.3f}')
    ax1.legend()
    
    # Plot 2: Spatial distribution
    ax2 = axes[1]
    scatter = ax2.scatter(
        coords[:, 0],
        coords[:, 1],
        c=confidences,
        cmap='viridis',
        s=20,
        alpha=0.6
    )
    ax2.set_xlabel('X (pixels)')
    ax2.set_ylabel('Y (pixels)')
    ax2.set_title('Spatial Distribution of Particles')
    ax2.invert_yaxis()  # Invert Y axis to match image coordinates
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax2)
    cbar.set_label('Confidence', rotation=270, labelpad=15)
    
    # Add statistics text
    stats_text = (
        f"Total particles: {len(coords)}\n"
        f"Mean confidence: {np.mean(confidences):.3f}\n"
        f"Std confidence: {np.std(confidences):.3f}"
    )
    fig.text(0.5, 0.02, stats_text, ha='center', fontsize=10, 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def read_star_file(filepath: str) -> Tuple[np.ndarray, np.ndarray, Optional[dict]]:
    """
    Read STAR file and extract particle coordinates and confidence scores.
    
    Args:
        filepath: Path to STAR file
        
    Returns:
        coords: Particle coordinates (N, 2) as [x, y]
        confidences: Confidence scores (N,)
        ctf_data: Optional dictionary with CTF parameters
    """
    coords = []
    confidences = []
    ctf_data = {}
    
    with open(filepath, 'r') as f:
        # Skip header lines
        in_data = False
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Check for data section
            if line.startswith('data_'):
                in_data = True
                continue
            
            # Skip loop_ and column headers
            if line.startswith('loop_') or line.startswith('_rln'):
                continue
            
            # Parse data lines
            if in_data:
                parts = line.split()
                if len(parts) >= 3:
                    x = float(parts[0])
                    y = float(parts[1])
                    conf = float(parts[2])
                    
                    coords.append([x, y])
                    confidences.append(conf)
                    
                    # Parse CTF data if available
                    if len(parts) >= 9:
                        ctf_data = {
                            'defocus_u': float(parts[3]),
                            'defocus_v': float(parts[4]),
                            'astigmatism_angle': float(parts[5]),
                            'astigmatism': float(parts[6]),
                            'max_resolution': float(parts[7]),
                            'fit_quality': float(parts[8])
                        }
    
    coords = np.array(coords)
    confidences = np.array(confidences)
    
    return coords, confidences, ctf_data if ctf_data else None


def create_advanced_visualizations(
    micrograph: np.ndarray,
    coords: np.ndarray,
    confidences: np.ndarray,
    output_dir: str,
    filename: str = "micrograph",
    particle_size: int = 200,
    ctf_params: Optional[CTFParameters] = None
) -> dict:
    """
    Create comprehensive visualization suite using the new standalone system.
    
    Args:
        micrograph: Input micrograph
        coords: Particle coordinates
        confidences: Confidence scores
        output_dir: Output directory
        filename: Base filename
        particle_size: Particle diameter
        ctf_params: CTF parameters (optional)
        
    Returns:
        Dictionary of created file paths
    """
    # Initialize visualization suite
    viz_suite = ParticleVisualizationSuite(use_plotly=True, style='publication')
    
    output_files = {}
    
    # 1. Particle overlay
    overlay_path = f"{output_dir}/{filename}_particle_overlay.png"
    viz_suite.create_particle_overlay(
        micrograph=micrograph,
        coords=coords,
        confidences=confidences,
        output_path=overlay_path,
        particle_size=particle_size,
        title=f"Particle Detection - {filename}",
        show_confidence=True,
        colormap='viridis'
    )
    output_files['overlay'] = overlay_path
    
    # 2. Confidence analysis
    confidence_path = f"{output_dir}/{filename}_confidence_analysis.png"
    viz_suite.create_confidence_analysis(
        coords=coords,
        confidences=confidences,
        output_path=confidence_path,
        title=f"Confidence Analysis - {filename}"
    )
    output_files['confidence'] = confidence_path
    
    # 3. Quality report
    report_path = f"{output_dir}/{filename}_quality_report.html"
    ctf_dict = None
    if ctf_params:
        ctf_dict = {
            'defocus_u': ctf_params.defocus_u,
            'defocus_v': ctf_params.defocus_v,
            'defocus_angle': ctf_params.defocus_angle,
            'voltage': ctf_params.voltage,
            'cs': ctf_params.cs,
            'pixel_size': ctf_params.pixel_size,
            'fit_resolution': ctf_params.fit_resolution,
            'fit_quality': ctf_params.fit_quality
        }
    
    viz_suite.create_quality_report(
        micrograph=micrograph,
        coords=coords,
        confidences=confidences,
        ctf_params=ctf_dict,
        output_path=report_path,
        filename=filename
    )
    output_files['report'] = report_path
    
    return output_files


def create_batch_visualization_summary(
    batch_results: list,
    output_path: str,
    title: str = "Batch Processing Summary"
) -> str:
    """
    Create batch processing summary visualization.
    
    Args:
        batch_results: List of batch processing results
        output_path: Output file path
        title: Plot title
        
    Returns:
        Path to created summary
    """
    viz_suite = ParticleVisualizationSuite(use_plotly=True, style='publication')
    
    return viz_suite.create_batch_summary(
        batch_results=batch_results,
        output_path=output_path,
        title=title
    )