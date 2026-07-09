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


def format_ai_label(text: Optional[str]) -> str:
    """Format raw variable or technical strings into publication-ready AI labels and titles."""
    if not text:
        return ""
    clean = str(text).replace('$', '').strip()
    abbrevs = {
        "id": "ID", "eur": "(EUR)", "usd": "(USD)", "gbp": "(GBP)", "pct": "(%)", 
        "cnt": "Count", "num": "Number", "avg": "Average", "std": "Standard Deviation",
        "max": "Maximum", "min": "Minimum", "lat": "Latitude", "lon": "Longitude",
        "pos": "Position", "grp": "Group", "dep": "Dependent", "ind": "Independent",
        "auc": "AUC", "roc": "ROC", "ols": "OLS", "anova": "ANOVA", "pca": "PCA"
    }
    # If the text already has nice mixed case or numbers and no underscores, preserve numbers & symbols
    words = clean.replace('_', ' ').split()
    formatted_words = []
    for w in words:
        clean_word = w.strip('(),:=')
        w_lower = clean_word.lower()
        if w_lower in abbrevs:
            formatted_words.append(w.replace(clean_word, abbrevs[w_lower]))
        elif clean_word.isupper() and len(clean_word) <= 5:
            formatted_words.append(w)
        else:
            # Capitalize word if it's all lowercase or starts with lower
            if w.islower() or (len(w) > 0 and w[0].islower()):
                formatted_words.append(w.capitalize())
            else:
                formatted_words.append(w)
    return " ".join(formatted_words)


def apply_statmind_theme(fig: go.Figure, title: Optional[str] = None, subtitle: Optional[str] = None) -> go.Figure:
    """Apply the Quantigen / StatMind professional publication theme to any Plotly figure."""
    clean_title = format_ai_label(title) if title else None
    clean_subtitle = subtitle.replace('$', '') if subtitle else None
    
    # Auto-format existing axis titles if they contain raw strings like player_id or market_value_eur
    if fig.layout.xaxis and fig.layout.xaxis.title and fig.layout.xaxis.title.text:
        current_x = fig.layout.xaxis.title.text
        if not current_x.endswith(")") and not current_x.isupper():
            fig.update_xaxes(title_text=format_ai_label(current_x))
            
    if fig.layout.yaxis and fig.layout.yaxis.title and fig.layout.yaxis.title.text:
        current_y = fig.layout.yaxis.title.text
        if not current_y.endswith(")") and not current_y.isupper():
            fig.update_yaxes(title_text=format_ai_label(current_y))
            
    # Auto-format trace names for clean legends
    for trace in fig.data:
        if hasattr(trace, 'name') and trace.name:
            trace.name = format_ai_label(str(trace.name))
    
    fig.update_layout(
        template="plotly_white",
        font=dict(
            family=STATMIND_THEME["font_family"],
            size=STATMIND_THEME["font_size"]["axis_tick"],
            color="#0f172a"
        ),
        plot_bgcolor=STATMIND_THEME["plot_background"],
        paper_bgcolor=STATMIND_THEME["background_color"],
        
        # Title
        title=dict(
            text=f"<b>{clean_title}</b>" + (f"<br><span style='font-size:12px;color:#475569;font-weight:normal;'>{clean_subtitle}</span>" if clean_subtitle else ""),
            font=dict(size=STATMIND_THEME["font_size"]["title"], color="#0f172a"),
            x=0,  # Left aligned
            xanchor="left",
            pad=dict(b=12)
        ) if clean_title else None,
        
        # Axes
        xaxis=dict(
            gridcolor=STATMIND_THEME["grid_color"],
            linecolor=STATMIND_THEME["border_color"],
            zerolinecolor=STATMIND_THEME["border_color"],
            title_font=dict(size=STATMIND_THEME["font_size"]["axis_title"], color="#0f172a", family="Inter, sans-serif"),
            tickfont=dict(size=STATMIND_THEME["font_size"]["axis_tick"], color="#334155"),
        ),
        yaxis=dict(
            gridcolor=STATMIND_THEME["grid_color"],
            linecolor=STATMIND_THEME["border_color"],
            zerolinecolor=STATMIND_THEME["border_color"],
            title_font=dict(size=STATMIND_THEME["font_size"]["axis_title"], color="#0f172a", family="Inter, sans-serif"),
            tickfont=dict(size=STATMIND_THEME["font_size"]["axis_tick"], color="#334155"),
        ),
        
        # Legend
        legend=dict(
            title=dict(text="<b>Series / Categories</b>", font=dict(size=11, color="#0f172a")),
            font=dict(size=STATMIND_THEME["font_size"]["legend"], color="#334155"),
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor=STATMIND_THEME["border_color"],
            borderwidth=1,
            x=1.02,
            xanchor="left",
            y=1,
            yanchor="top"
        ),
        
        # Margins
        margin=dict(l=65, r=140 if any(t.showlegend is not False for t in fig.data) else 40, t=75, b=65),
        
        # Remove plotly branding
        modebar_remove=["sendDataToCloud"],
    )
    
    return fig


QUANTIGEN_THEME = STATMIND_THEME
apply_quantigen_theme = apply_statmind_theme
