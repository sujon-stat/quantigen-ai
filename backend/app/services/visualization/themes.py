import plotly.graph_objects as go
from typing import Optional


STATMIND_THEME = {
    # Color palette - inspired by ggplot2's default but more modern
    "colors": {
        "primary": "#2E86AB",       # Steel blue
        "secondary": "#A23B72",     # Berry
        "tertiary": "#F18F01",      # Amber
        "quaternary": "#C73E1D",    # Rust
        "quinary": "#3B1F2B",       # Dark plum
        "success": "#2ECC71",       # Green
        "warning": "#F39C12",       # Orange
        "error": "#E74C3C",         # Red
        "neutral": "#95A5A6",       # Gray
    },
    
    "categorical_palette": [
        "#2E86AB", "#A23B72", "#F18F01", "#C73E1D", 
        "#3B1F2B", "#44BBA4", "#E94F37", "#393E41",
        "#8EE3EF", "#F6D55C"
    ],
    
    # Font
    "font_family": "'Inter', 'Segoe UI', sans-serif",
    "font_size": {
        "title": 16,
        "subtitle": 13,
        "axis_title": 13,
        "axis_tick": 11,
        "annotation": 11,
        "legend": 11,
    },
    
    # Layout
    "background_color": "#FFFFFF",
    "plot_background": "#FAFAFA",
    "grid_color": "#E8E8E8",
    "border_color": "#DDDDDD",
    
    # Sizes
    "default_width": 700,
    "default_height": 500,
    "default_margin": {"l": 60, "r": 30, "t": 60, "b": 60},
}


def apply_statmind_theme(fig: go.Figure, title: Optional[str] = None, subtitle: Optional[str] = None) -> go.Figure:
    """Apply the StatMind professional theme to any Plotly figure."""
    
    fig.update_layout(
        template="plotly_white",
        font=dict(
            family=STATMIND_THEME["font_family"],
            size=STATMIND_THEME["font_size"]["axis_tick"],
            color="#333333"
        ),
        plot_bgcolor=STATMIND_THEME["plot_background"],
        paper_bgcolor=STATMIND_THEME["background_color"],
        
        # Title
        title=dict(
            text=f"<b>{title}</b>" + (f"<br><sup>{subtitle}</sup>" if subtitle else ""),
            font=dict(size=STATMIND_THEME["font_size"]["title"]),
            x=0,  # Left aligned
            xanchor="left",
            pad=dict(b=10)
        ) if title else None,
        
        # Axes
        xaxis=dict(
            gridcolor=STATMIND_THEME["grid_color"],
            linecolor=STATMIND_THEME["border_color"],
            zerolinecolor=STATMIND_THEME["border_color"],
            title_font=dict(size=STATMIND_THEME["font_size"]["axis_title"]),
            tickfont=dict(size=STATMIND_THEME["font_size"]["axis_tick"]),
        ),
        yaxis=dict(
            gridcolor=STATMIND_THEME["grid_color"],
            linecolor=STATMIND_THEME["border_color"],
            zerolinecolor=STATMIND_THEME["border_color"],
            title_font=dict(size=STATMIND_THEME["font_size"]["axis_title"]),
            tickfont=dict(size=STATMIND_THEME["font_size"]["axis_tick"]),
        ),
        
        # Legend
        legend=dict(
            font=dict(size=STATMIND_THEME["font_size"]["legend"]),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=STATMIND_THEME["border_color"],
            borderwidth=1,
        ),
        
        # Margins
        margin=STATMIND_THEME["default_margin"],
        
        # Remove plotly branding
        modebar_remove=["sendDataToCloud"],
    )
    
    return fig
