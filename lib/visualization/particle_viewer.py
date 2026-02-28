"""
Standalone particle visualization system
Creates comprehensive visualizations from STAR files without RELION/CryoSPARC
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import json

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from ..error_handling import FileIOError, ProcessingError


class ParticleVisualizationSuite:
    """
    Comprehensive particle visualization suite for CryoEM data.
    
    Creates publication-quality visualizations including:
    - Particle pick overlays on micrographs
    - Confidence heatmaps and distributions
    - Statistical analysis plots
    - Interactive 3D visualizations
    - Batch processing summaries
    - Quality assessment reports
    """
    
    def __init__(self, use_plotly: bool = True, style: str = 'publication'):
        """
        Initialize visualization suite.
        
        Args:
            use_plotly: Use Plotly for interactive plots
            style: Visualization style ('publication', 'presentation', 'web')
        """
        self.use_plotly = use_plotly and PLOTLY_AVAILABLE
        self.style = style
        
        # Set up matplotlib style
        self._setup_matplotlib_style()
        
        # Color schemes
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72', 
            'accent': '#F18F01',
            'success': '#C73E1D',
            'background': '#F5F5F5',
            'text': '#2C3E50'
        }
    
    def _setup_matplotlib_style(self):
        """Setup matplotlib styling for publication quality."""
        plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
        
        # Custom parameters
        params = {
            'figure.figsize': (12, 8),
            'figure.dpi': 300,
            'savefig.dpi': 300,
            'font.size': 12,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans']
        }
        
        if self.style == 'publication':
            params.update({
                'figure.figsize': (10, 6),
                'font.size': 11,
                'axes.linewidth': 1.2,
                'grid.alpha': 0.3
            })
        elif self.style == 'presentation':
            params.update({
                'figure.figsize': (14, 10),
                'font.size': 16,
                'axes.titlesize': 20,
                'axes.labelsize': 16
            })
        
        plt.rcParams.update(params)
    
    def create_particle_overlay(
        self,
        micrograph: np.ndarray,
        coords: np.ndarray,
        confidences: np.ndarray,
        output_path: str,
        particle_size: int = 200,
        title: str = "Particle Picks",
        show_confidence: bool = True,
        colormap: str = 'viridis'
    ) -> str:
        """
        Create particle pick overlay on micrograph.
        
        Args:
            micrograph: Input micrograph
            coords: Particle coordinates (N, 2)
            confidences: Confidence scores (N,)
            output_path: Output file path
            particle_size: Particle diameter for circles
            title: Plot title
            show_confidence: Color circles by confidence
            colormap: Colormap for confidence visualization
            
        Returns:
            Path to saved visualization
        """
        if self.use_plotly:
            return self._create_plotly_overlay(
                micrograph, coords, confidences, output_path,
                particle_size, title, show_confidence, colormap
            )
        else:
            return self._create_matplotlib_overlay(
                micrograph, coords, confidences, output_path,
                particle_size, title, show_confidence, colormap
            )
    
    def _create_matplotlib_overlay(
        self,
        micrograph: np.ndarray,
        coords: np.ndarray,
        confidences: np.ndarray,
        output_path: str,
        particle_size: int,
        title: str,
        show_confidence: bool,
        colormap: str
    ) -> str:
        """Create matplotlib-based overlay."""
        
        fig, ax = plt.subplots(1, 1, figsize=(16, 12))
        
        # Display micrograph
        im = ax.imshow(micrograph, cmap='gray', alpha=0.8)
        
        # Add particles
        if len(coords) > 0:
            if show_confidence and len(confidences) > 0:
                # Color by confidence
                scatter = ax.scatter(
                    coords[:, 0], coords[:, 1],
                    c=confidences,
                    cmap=colormap,
                    s=particle_size/4,
                    alpha=0.7,
                    edgecolors='white',
                    linewidth=2
                )
                
                # Add colorbar
                cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
                cbar.set_label('Confidence Score', fontsize=12)
                
                # Add circles
                for (x, y), conf in zip(coords, confidences):
                    circle = patches.Circle(
                        (x, y), particle_size/2,
                        fill=False,
                        edgecolor=plt.cm.get_cmap(colormap)(conf),
                        linewidth=2,
                        alpha=0.8
                    )
                    ax.add_patch(circle)
            else:
                # Single color
                ax.scatter(
                    coords[:, 0], coords[:, 1],
                    c=self.colors['accent'],
                    s=particle_size/4,
                    alpha=0.7,
                    edgecolors='white',
                    linewidth=2
                )
                
                # Add circles
                for x, y in coords:
                    circle = patches.Circle(
                        (x, y), particle_size/2,
                        fill=False,
                        edgecolor=self.colors['accent'],
                        linewidth=2,
                        alpha=0.8
                    )
                    ax.add_patch(circle)
        
        # Formatting
        ax.set_title(f'{title}\n{len(coords)} particles detected', fontsize=16, pad=20)
        ax.set_xlabel('X (pixels)', fontsize=12)
        ax.set_ylabel('Y (pixels)', fontsize=12)
        
        # Add statistics text
        if len(coords) > 0 and len(confidences) > 0:
            stats_text = f"""Statistics:
Particles: {len(coords)}
Mean confidence: {confidences.mean():.3f}
Std confidence: {confidences.std():.3f}
Min confidence: {confidences.min():.3f}
Max confidence: {confidences.max():.3f}"""
            
            ax.text(
                0.02, 0.98, stats_text,
                transform=ax.transAxes,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                fontsize=10
            )
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def _create_plotly_overlay(
        self,
        micrograph: np.ndarray,
        coords: np.ndarray,
        confidences: np.ndarray,
        output_path: str,
        particle_size: int,
        title: str,
        show_confidence: bool,
        colormap: str
    ) -> str:
        """Create Plotly-based interactive overlay."""
        
        fig = go.Figure()
        
        # Add micrograph as heatmap
        fig.add_trace(go.Heatmap(
            z=micrograph,
            colorscale='gray',
            showscale=False,
            hovertemplate='X: %{x}<br>Y: %{y}<br>Intensity: %{z}<extra></extra>'
        ))
        
        # Add particles
        if len(coords) > 0:
            if show_confidence and len(confidences) > 0:
                fig.add_trace(go.Scatter(
                    x=coords[:, 0],
                    y=coords[:, 1],
                    mode='markers',
                    marker=dict(
                        size=particle_size/8,
                        color=confidences,
                        colorscale=colormap,
                        showscale=True,
                        colorbar=dict(title="Confidence"),
                        line=dict(width=2, color='white')
                    ),
                    text=[f'Confidence: {conf:.3f}' for conf in confidences],
                    hovertemplate='X: %{x}<br>Y: %{y}<br>%{text}<extra></extra>',
                    name='Particles'
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=coords[:, 0],
                    y=coords[:, 1],
                    mode='markers',
                    marker=dict(
                        size=particle_size/8,
                        color=self.colors['accent'],
                        line=dict(width=2, color='white')
                    ),
                    hovertemplate='X: %{x}<br>Y: %{y}<extra></extra>',
                    name='Particles'
                ))
        
        # Layout
        fig.update_layout(
            title=f'{title}<br>{len(coords)} particles detected',
            xaxis_title='X (pixels)',
            yaxis_title='Y (pixels)',
            width=1200,
            height=900,
            showlegend=True
        )
        
        # Save as HTML
        html_path = output_path.replace('.png', '.html')
        fig.write_html(html_path)
        
        # Also save as static image
        if output_path.endswith('.png'):
            fig.write_image(output_path, width=1200, height=900, scale=2)
        
        return output_path
    
    def create_confidence_analysis(
        self,
        coords: np.ndarray,
        confidences: np.ndarray,
        output_path: str,
        title: str = "Confidence Analysis"
    ) -> str:
        """Create comprehensive confidence analysis plots."""
        
        if len(coords) == 0:
            # Create empty plot
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            ax.text(0.5, 0.5, 'No particles detected', 
                   ha='center', va='center', fontsize=16)
            ax.set_title(title)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            return output_path
        
        if self.use_plotly:
            return self._create_plotly_confidence_analysis(coords, confidences, output_path, title)
        else:
            return self._create_matplotlib_confidence_analysis(coords, confidences, output_path, title)
    
    def _create_matplotlib_confidence_analysis(
        self,
        coords: np.ndarray,
        confidences: np.ndarray,
        output_path: str,
        title: str
    ) -> str:
        """Create matplotlib confidence analysis."""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Confidence histogram
        ax1.hist(confidences, bins=30, alpha=0.7, color=self.colors['primary'], edgecolor='black')
        ax1.axvline(confidences.mean(), color=self.colors['accent'], linestyle='--', 
                   label=f'Mean: {confidences.mean():.3f}')
        ax1.set_xlabel('Confidence Score')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Confidence Distribution')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Confidence vs Position (X)
        ax2.scatter(coords[:, 0], confidences, alpha=0.6, color=self.colors['secondary'])
        ax2.set_xlabel('X Position (pixels)')
        ax2.set_ylabel('Confidence Score')
        ax2.set_title('Confidence vs X Position')
        ax2.grid(True, alpha=0.3)
        
        # 3. Confidence vs Position (Y)
        ax3.scatter(coords[:, 1], confidences, alpha=0.6, color=self.colors['success'])
        ax3.set_xlabel('Y Position (pixels)')
        ax3.set_ylabel('Confidence Score')
        ax3.set_title('Confidence vs Y Position')
        ax3.grid(True, alpha=0.3)
        
        # 4. Statistics summary
        stats = {
            'Count': len(confidences),
            'Mean': confidences.mean(),
            'Std': confidences.std(),
            'Min': confidences.min(),
            'Max': confidences.max(),
            'Q25': np.percentile(confidences, 25),
            'Q50': np.percentile(confidences, 50),
            'Q75': np.percentile(confidences, 75)
        }
        
        ax4.axis('off')
        stats_text = '\n'.join([f'{k}: {v:.3f}' if isinstance(v, float) else f'{k}: {v}' 
                               for k, v in stats.items()])
        ax4.text(0.1, 0.9, 'Statistics Summary:', fontsize=14, fontweight='bold',
                transform=ax4.transAxes)
        ax4.text(0.1, 0.7, stats_text, fontsize=12, transform=ax4.transAxes,
                verticalalignment='top', fontfamily='monospace')
        
        # Box plot
        box_data = [confidences]
        bp = ax4.boxplot(box_data, positions=[0.7], widths=0.1, patch_artist=True,
                        vert=False)
        bp['boxes'][0].set_facecolor(self.colors['primary'])
        bp['boxes'][0].set_alpha(0.7)
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0.5, 1)
        
        plt.suptitle(title, fontsize=16, y=0.98)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def create_batch_summary(
        self,
        batch_results: List[Dict[str, Any]],
        output_path: str,
        title: str = "Batch Processing Summary"
    ) -> str:
        """Create batch processing summary visualization."""
        
        if not batch_results:
            return self._create_empty_summary(output_path, title)
        
        # Extract data
        filenames = [r['filename'] for r in batch_results]
        particle_counts = [r['particle_count'] for r in batch_results]
        mean_confidences = [r['mean_confidence'] for r in batch_results if r['mean_confidence'] is not None]
        processing_times = [r['processing_time'] for r in batch_results]
        
        if self.use_plotly:
            return self._create_plotly_batch_summary(
                filenames, particle_counts, mean_confidences, processing_times, output_path, title
            )
        else:
            return self._create_matplotlib_batch_summary(
                filenames, particle_counts, mean_confidences, processing_times, output_path, title
            )
    
    def _create_matplotlib_batch_summary(
        self,
        filenames: List[str],
        particle_counts: List[int],
        mean_confidences: List[float],
        processing_times: List[float],
        output_path: str,
        title: str
    ) -> str:
        """Create matplotlib batch summary."""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 12))
        
        # 1. Particle counts per file
        bars1 = ax1.bar(range(len(filenames)), particle_counts, color=self.colors['primary'], alpha=0.7)
        ax1.set_xlabel('File Index')
        ax1.set_ylabel('Particle Count')
        ax1.set_title('Particles per Micrograph')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for i, (bar, count) in enumerate(zip(bars1, particle_counts)):
            if count > 0:
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(particle_counts)*0.01,
                        str(count), ha='center', va='bottom', fontsize=8)
        
        # 2. Mean confidence distribution
        if mean_confidences:
            ax2.hist(mean_confidences, bins=20, color=self.colors['secondary'], alpha=0.7, edgecolor='black')
            ax2.axvline(np.mean(mean_confidences), color=self.colors['accent'], linestyle='--',
                       label=f'Overall Mean: {np.mean(mean_confidences):.3f}')
            ax2.set_xlabel('Mean Confidence')
            ax2.set_ylabel('Frequency')
            ax2.set_title('Mean Confidence Distribution')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        else:
            ax2.text(0.5, 0.5, 'No confidence data', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Mean Confidence Distribution')
        
        # 3. Processing times
        bars3 = ax3.bar(range(len(filenames)), processing_times, color=self.colors['success'], alpha=0.7)
        ax3.set_xlabel('File Index')
        ax3.set_ylabel('Processing Time (s)')
        ax3.set_title('Processing Time per File')
        ax3.grid(True, alpha=0.3)
        
        # 4. Summary statistics
        ax4.axis('off')
        
        total_particles = sum(particle_counts)
        total_time = sum(processing_times)
        avg_particles = np.mean(particle_counts) if particle_counts else 0
        avg_confidence = np.mean(mean_confidences) if mean_confidences else 0
        avg_time = np.mean(processing_times) if processing_times else 0
        
        summary_stats = f"""Batch Processing Summary:
        
Files processed: {len(filenames)}
Total particles: {total_particles:,}
Average particles per file: {avg_particles:.1f}
Average confidence: {avg_confidence:.3f}
Total processing time: {total_time:.1f}s
Average time per file: {avg_time:.1f}s
Throughput: {len(filenames)/total_time*3600:.1f} files/hour"""
        
        ax4.text(0.05, 0.95, summary_stats, transform=ax4.transAxes,
                verticalalignment='top', fontsize=12, fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor=self.colors['background'], alpha=0.8))
        
        plt.suptitle(title, fontsize=16, y=0.98)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def create_quality_report(
        self,
        micrograph: np.ndarray,
        coords: np.ndarray,
        confidences: np.ndarray,
        ctf_params: Optional[Dict] = None,
        output_path: str = None,
        filename: str = "micrograph"
    ) -> str:
        """Create comprehensive quality assessment report."""
        
        if output_path is None:
            output_path = f"{filename}_quality_report.html"
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(micrograph, coords, confidences, ctf_params)
        
        # Generate HTML report
        html_content = self._generate_html_report(quality_metrics, filename)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        return output_path
    
    def _calculate_quality_metrics(
        self,
        micrograph: np.ndarray,
        coords: np.ndarray,
        confidences: np.ndarray,
        ctf_params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Calculate comprehensive quality metrics."""
        
        metrics = {
            'micrograph': {
                'shape': micrograph.shape,
                'mean_intensity': float(micrograph.mean()),
                'std_intensity': float(micrograph.std()),
                'min_intensity': float(micrograph.min()),
                'max_intensity': float(micrograph.max()),
                'contrast': float(micrograph.std() / micrograph.mean()) if micrograph.mean() != 0 else 0
            },
            'particles': {
                'count': len(coords),
                'density': len(coords) / (micrograph.shape[0] * micrograph.shape[1]) * 1e6,  # particles per megapixel
            }
        }
        
        if len(confidences) > 0:
            metrics['particles'].update({
                'mean_confidence': float(confidences.mean()),
                'std_confidence': float(confidences.std()),
                'min_confidence': float(confidences.min()),
                'max_confidence': float(confidences.max()),
                'high_confidence_fraction': float((confidences > 0.8).sum() / len(confidences))
            })
        
        if ctf_params:
            metrics['ctf'] = ctf_params
        
        return metrics
    
    def _generate_html_report(self, metrics: Dict[str, Any], filename: str) -> str:
        """Generate HTML quality report."""
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CryoEM Quality Report - {filename}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2E86AB; border-bottom: 3px solid #2E86AB; padding-bottom: 10px; }}
        h2 {{ color: #A23B72; margin-top: 30px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #F18F01; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2E86AB; }}
        .metric-label {{ color: #666; font-size: 14px; }}
        .quality-indicator {{ display: inline-block; padding: 5px 15px; border-radius: 20px; color: white; font-weight: bold; }}
        .excellent {{ background-color: #28a745; }}
        .good {{ background-color: #17a2b8; }}
        .fair {{ background-color: #ffc107; color: #212529; }}
        .poor {{ background-color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #2E86AB; color: white; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔬 CryoEM Quality Assessment Report</h1>
        <p><strong>File:</strong> {filename}</p>
        <p><strong>Generated:</strong> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>📊 Micrograph Quality</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{metrics['micrograph']['shape'][0]} × {metrics['micrograph']['shape'][1]}</div>
                <div class="metric-label">Image Dimensions (pixels)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics['micrograph']['contrast']:.3f}</div>
                <div class="metric-label">Contrast Ratio</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics['micrograph']['std_intensity']:.2f}</div>
                <div class="metric-label">Intensity Standard Deviation</div>
            </div>
        </div>
        
        <h2>🎯 Particle Detection Results</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{metrics['particles']['count']:,}</div>
                <div class="metric-label">Total Particles Detected</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics['particles']['density']:.1f}</div>
                <div class="metric-label">Particle Density (per megapixel)</div>
            </div>
        """
        
        if 'mean_confidence' in metrics['particles']:
            confidence_quality = "excellent" if metrics['particles']['mean_confidence'] > 0.8 else \
                               "good" if metrics['particles']['mean_confidence'] > 0.6 else \
                               "fair" if metrics['particles']['mean_confidence'] > 0.4 else "poor"
            
            html += f"""
            <div class="metric-card">
                <div class="metric-value">{metrics['particles']['mean_confidence']:.3f}</div>
                <div class="metric-label">Mean Confidence Score</div>
                <div class="quality-indicator {confidence_quality}">
                    {confidence_quality.upper()}
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics['particles']['high_confidence_fraction']*100:.1f}%</div>
                <div class="metric-label">High Confidence Particles (>0.8)</div>
            </div>
            """
        
        html += """
        </div>
        
        <h2>📋 Detailed Metrics</h2>
        <table>
            <tr><th>Parameter</th><th>Value</th><th>Description</th></tr>
        """
        
        # Add detailed metrics table
        detailed_metrics = [
            ("Image Size", f"{metrics['micrograph']['shape'][0]} × {metrics['micrograph']['shape'][1]} pixels", "Micrograph dimensions"),
            ("Mean Intensity", f"{metrics['micrograph']['mean_intensity']:.3f}", "Average pixel intensity"),
            ("Intensity Range", f"{metrics['micrograph']['min_intensity']:.3f} - {metrics['micrograph']['max_intensity']:.3f}", "Min and max pixel values"),
            ("Contrast", f"{metrics['micrograph']['contrast']:.3f}", "Standard deviation / mean intensity"),
            ("Particle Count", f"{metrics['particles']['count']:,}", "Total detected particles"),
            ("Particle Density", f"{metrics['particles']['density']:.2f} /Mpx", "Particles per megapixel"),
        ]
        
        if 'mean_confidence' in metrics['particles']:
            detailed_metrics.extend([
                ("Mean Confidence", f"{metrics['particles']['mean_confidence']:.3f}", "Average detection confidence"),
                ("Confidence Range", f"{metrics['particles']['min_confidence']:.3f} - {metrics['particles']['max_confidence']:.3f}", "Min and max confidence scores"),
                ("Confidence Std", f"{metrics['particles']['std_confidence']:.3f}", "Confidence score variability"),
            ])
        
        for param, value, desc in detailed_metrics:
            html += f"<tr><td><strong>{param}</strong></td><td>{value}</td><td>{desc}</td></tr>"
        
        html += """
        </table>
        
        <div class="footer">
            <p>Generated by CryoEM Particle Picker - Advanced Visualization Suite</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    def _create_empty_summary(self, output_path: str, title: str) -> str:
        """Create empty summary for no results."""
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        ax.text(0.5, 0.5, 'No batch results to display', 
               ha='center', va='center', fontsize=16)
        ax.set_title(title)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return output_path