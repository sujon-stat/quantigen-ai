import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats
from typing import Any, Dict, List, Optional
from backend.app.services.visualization.themes import STATMIND_THEME, apply_statmind_theme


def fig_to_dict(fig: go.Figure) -> Dict[str, Any]:
    """Convert Plotly go.Figure to JSON-serializable dictionary for frontend."""
    return json.loads(fig.to_json())


def plot_boxplot_jitter(
    data: pd.DataFrame,
    dep_var: str,
    group_var: str,
    title: str,
    subtitle: Optional[str] = None
) -> Dict[str, Any]:
    """Generate side-by-side box plots with jittered data points and mean diamonds."""
    df_clean = data[[dep_var, group_var]].dropna()
    groups = df_clean[group_var].unique()
    
    fig = go.Figure()
    
    for i, grp in enumerate(groups):
        grp_data = df_clean[df_clean[group_var] == grp][dep_var]
        color = STATMIND_THEME["categorical_palette"][i % len(STATMIND_THEME["categorical_palette"])]
        
        # Add box plot with jitter
        fig.add_trace(go.Box(
            y=grp_data,
            name=str(grp),
            boxpoints='all',
            jitter=0.25,
            pointpos=-1.5,
            marker=dict(color=color, size=4, opacity=0.45),
            line=dict(color=color, width=2),
            fillcolor=color,
            opacity=0.8,
            showlegend=False
        ))
        
        # Add mean diamond
        mean_val = float(grp_data.mean())
        fig.add_trace(go.Scatter(
            x=[str(grp)],
            y=[mean_val],
            mode='markers',
            marker=dict(symbol='diamond', size=10, color='white', line=dict(color='#333333', width=2)),
            name=f"{grp} Mean ({mean_val:.2f})",
            hoverinfo='name+y'
        ))
        
    if not subtitle:
        n_str = ", ".join([f"n({g})={sum(df_clean[group_var] == g)}" for g in groups])
        subtitle = f"Sample Sizes: {n_str}"
        
    fig.update_xaxes(title_text=group_var)
    fig.update_yaxes(title_text=dep_var)
    
    fig = apply_statmind_theme(fig, title=title, subtitle=subtitle)
    return fig_to_dict(fig)


def plot_qq_normality(
    series_dict: Dict[str, pd.Series],
    title: str,
    subtitle: Optional[str] = None
) -> Dict[str, Any]:
    """Generate Q-Q plots for normality checking against theoretical normal quantiles."""
    fig = go.Figure()
    
    for i, (name, series) in enumerate(series_dict.items()):
        clean_s = series.dropna()
        if len(clean_s) < 3:
            continue
            
        color = STATMIND_THEME["categorical_palette"][i % len(STATMIND_THEME["categorical_palette"])]
        
        # Theoretical and sample quantiles
        sorted_data = np.sort(clean_s)
        n = len(sorted_data)
        theoretical_q = stats.norm.ppf((np.arange(1, n + 1) - 0.5) / n)
        
        # Fit reference line
        slope, intercept, _, _, _ = stats.linregress(theoretical_q, sorted_data)
        ref_y = slope * theoretical_q + intercept
        
        fig.add_trace(go.Scatter(
            x=theoretical_q,
            y=sorted_data,
            mode='markers',
            name=f"{name} Quantiles",
            marker=dict(color=color, size=6, opacity=0.7)
        ))
        
        fig.add_trace(go.Scatter(
            x=theoretical_q,
            y=ref_y,
            mode='lines',
            name=f"{name} Normal Fit",
            line=dict(color=color, dash='dash', width=1.5)
        ))
        
    fig.update_xaxes(title_text="Theoretical Quantiles (Standard Normal)")
    fig.update_yaxes(title_text="Sample Quantiles")
    
    fig = apply_statmind_theme(fig, title=title, subtitle=subtitle)
    return fig_to_dict(fig)


def plot_scatter_regression(
    data: pd.DataFrame,
    x_var: str,
    y_var: str,
    title: str,
    subtitle: Optional[str] = None
) -> Dict[str, Any]:
    """Generate scatter plot with OLS regression line and 95% confidence interval bands."""
    df_clean = data[[x_var, y_var]].dropna().sort_values(by=x_var)
    x = df_clean[x_var].values
    y = df_clean[y_var].values
    n = len(x)
    
    fig = go.Figure()
    
    # Scatter points
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='markers',
        name='Observations',
        marker=dict(color=STATMIND_THEME["colors"]["primary"], size=7, opacity=0.65)
    ))
    
    if n > 2:
        # Fit OLS line and CI
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        y_pred = slope * x + intercept
        
        # Calculate 95% CI bands for mean prediction
        x_mean = np.mean(x)
        s_err = np.sqrt(np.sum((y - y_pred)**2) / (n - 2))
        t_val = stats.t.ppf(0.975, df=n-2)
        ci_half = t_val * s_err * np.sqrt(1/n + ((x - x_mean)**2) / np.sum((x - x_mean)**2))
        
        ci_upper = y_pred + ci_half
        ci_lower = y_pred - ci_half
        
        # Add CI fill band
        fig.add_trace(go.Scatter(
            x=np.concatenate([x, x[::-1]]),
            y=np.concatenate([ci_upper, ci_lower[::-1]]),
            fill='toself',
            fillcolor='rgba(46, 134, 171, 0.15)',
            line=dict(color='rgba(255,255,255,0)'),
            name='95% Confidence Band',
            hoverinfo='skip'
        ))
        
        # Add regression line
        fig.add_trace(go.Scatter(
            x=x,
            y=y_pred,
            mode='lines',
            name=f'OLS Fit (r = {r_value:.2f}, p = {p_value:.3f})',
            line=dict(color=STATMIND_THEME["colors"]["quaternary"], width=2.5)
        ))
        
    fig.update_xaxes(title_text=x_var)
    fig.update_yaxes(title_text=y_var)
    
    fig = apply_statmind_theme(fig, title=title, subtitle=subtitle or f"Sample Size: n = {n}")
    return fig_to_dict(fig)


def plot_grouped_bar(
    crosstab_df: pd.DataFrame,
    title: str,
    subtitle: Optional[str] = None
) -> Dict[str, Any]:
    """Generate grouped bar chart for cross-tabulated categorical variables."""
    fig = go.Figure()
    
    for i, col in enumerate(crosstab_df.columns):
        color = STATMIND_THEME["categorical_palette"][i % len(STATMIND_THEME["categorical_palette"])]
        fig.add_trace(go.Bar(
            name=str(col),
            x=crosstab_df.index.astype(str),
            y=crosstab_df[col],
            marker=dict(color=color)
        ))
        
    fig.update_layout(barmode='group')
    fig.update_xaxes(title_text=str(crosstab_df.index.name or "Category"))
    fig.update_yaxes(title_text="Observed Count")
    
    fig = apply_statmind_theme(fig, title=title, subtitle=subtitle)
    return fig_to_dict(fig)


def plot_residual_heatmap(
    observed: pd.DataFrame,
    expected: pd.DataFrame,
    title: str,
    subtitle: Optional[str] = None
) -> Dict[str, Any]:
    """Generate Pearson residual heatmap ((O - E) / sqrt(E)) for chi-square table."""
    residuals = (observed - expected) / np.sqrt(expected)
    
    fig = go.Figure(data=go.Heatmap(
        z=residuals.values,
        x=residuals.columns.astype(str),
        y=residuals.index.astype(str),
        colorscale='RdBu_r',
        zmid=0,
        text=np.round(residuals.values, 2),
        texttemplate="%{text}",
        colorbar=dict(title="Standardized<br>Residual")
    ))
    
    fig.update_xaxes(title_text=str(observed.columns.name or "Column Category"))
    fig.update_yaxes(title_text=str(observed.index.name or "Row Category"))
    
    fig = apply_statmind_theme(fig, title=title, subtitle=subtitle or "Red/Blue indicate cells higher/lower than independence expectation")
    return fig_to_dict(fig)


def plot_residuals_vs_fitted(
    fitted_values: pd.Series,
    residuals: pd.Series,
    title: str,
    subtitle: Optional[str] = None
) -> Dict[str, Any]:
    """Generate Residuals vs Fitted plot for regression linearity and homoscedasticity diagnostics."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=fitted_values,
        y=residuals,
        mode='markers',
        name='Residuals',
        marker=dict(color=STATMIND_THEME["colors"]["primary"], size=7, opacity=0.65)
    ))
    
    # Horizontal zero line
    fig.add_hline(y=0, line_dash="dash", line_color=STATMIND_THEME["colors"]["error"], line_width=2)
    
    fig.update_xaxes(title_text="Fitted Values (Predicted Y)")
    fig.update_yaxes(title_text="Residuals (Observed Y - Predicted Y)")
    
    fig = apply_statmind_theme(fig, title=title, subtitle=subtitle or "Random scatter around horizontal zero line indicates good model fit")
    return fig_to_dict(fig)


def plot_logistic_probabilities(
    fitted_probs: pd.Series,
    actual_y: pd.Series,
    title: str,
    subtitle: Optional[str] = None
) -> Dict[str, Any]:
    """Generate predicted probability distribution plot separated by actual binary outcome."""
    fig = go.Figure()
    
    unique_classes = sorted(actual_y.dropna().unique())
    for i, cls in enumerate(unique_classes):
        probs = fitted_probs[actual_y == cls].dropna()
        color = STATMIND_THEME["categorical_palette"][i % len(STATMIND_THEME["categorical_palette"])]
        
        # We plot a histogram / density approximation or boxplot/violin of predicted probabilities
        fig.add_trace(go.Box(
            x=probs,
            name=f"Actual Outcome = {cls} (n={len(probs)})",
            boxpoints='all',
            jitter=0.3,
            pointpos=-1.5,
            marker=dict(color=color, size=5, opacity=0.5),
            line=dict(color=color, width=2),
            fillcolor=color,
            opacity=0.8
        ))
        
    fig.add_vline(x=0.5, line_dash="dash", line_color="#888888", annotation_text="Classification Threshold (0.50)")
    fig.update_xaxes(title_text="Predicted Probability P(Outcome = 1)", range=[-0.05, 1.05])
    fig.update_yaxes(title_text="Actual Binary Outcome Class")
    
    fig = apply_statmind_theme(fig, title=title, subtitle=subtitle or "Comparison of predicted event probabilities between binary classes")
    return fig_to_dict(fig)


def plot_forest_odds_ratios(
    conf_int_df: pd.DataFrame,
    title: str,
    subtitle: Optional[str] = None
) -> Dict[str, Any]:
    """Generate Forest Plot of Odds Ratios with 95% Confidence Intervals (log-scale x-axis)."""
    fig = go.Figure()
    
    df = conf_int_df.copy()
    if 'Odds_Ratio' not in df.columns and 'OR' in df.columns:
        df['Odds_Ratio'] = df['OR']
    if 'CI_Lower' not in df.columns and 'CI_lower' in df.columns:
        df['CI_Lower'] = df['CI_lower']
    if 'CI_Upper' not in df.columns and 'CI_upper' in df.columns:
        df['CI_Upper'] = df['CI_upper']
        
    # Reverse rows so first predictor is at the top of the y-axis
    df = df.iloc[::-1]
    
    y_labels = df.index.astype(str).tolist()
    x_or = df['Odds_Ratio'].tolist()
    x_lower = df['CI_Lower'].tolist()
    x_upper = df['CI_Upper'].tolist()
    
    error_minus = [max(0.0, o - l) if not np.isnan(o) and not np.isnan(l) else 0.0 for o, l in zip(x_or, x_lower)]
    error_plus = [max(0.0, u - o) if not np.isnan(o) and not np.isnan(u) else 0.0 for o, u in zip(x_or, x_upper)]
    
    fig.add_trace(go.Scatter(
        x=x_or,
        y=y_labels,
        mode='markers',
        name='Odds Ratio (95% CI)',
        error_x=dict(
            type='data',
            symmetric=False,
            array=error_plus,
            arrayminus=error_minus,
            color=STATMIND_THEME["colors"]["primary"],
            thickness=2,
            width=6
        ),
        marker=dict(color=STATMIND_THEME["colors"]["primary"], size=10, symbol='square')
    ))
    
    fig.add_vline(x=1.0, line_dash="dash", line_color=STATMIND_THEME["colors"]["error"], line_width=2, annotation_text="No Effect (OR=1.0)")
    fig.update_xaxes(title_text="Odds Ratio (Log Scale)", type="log")
    fig.update_yaxes(title_text="Predictor Variable")
    
    fig = apply_statmind_theme(fig, title=title, subtitle=subtitle or "Horizontal bars crossing 1.0 indicate non-significant predictors at alpha=0.05")
    return fig_to_dict(fig)


def plot_forest_coefficients(
    params_df: pd.DataFrame,
    title: str,
    subtitle: Optional[str] = None
) -> Dict[str, Any]:
    """Generate Forest Plot of OLS Regression Coefficients with 95% Confidence Intervals."""
    fig = go.Figure()
    
    df = params_df.copy()
    if 'coef' not in df.columns and 'Beta' in df.columns:
        df['coef'] = df['Beta']
        
    df = df.iloc[::-1]
    y_labels = df.index.astype(str).tolist()
    x_coef = df['coef'].tolist()
    x_lower = df['CI_Lower'].tolist()
    x_upper = df['CI_Upper'].tolist()
    
    error_minus = [max(0.0, c - l) if not np.isnan(c) and not np.isnan(l) else 0.0 for c, l in zip(x_coef, x_lower)]
    error_plus = [max(0.0, u - c) if not np.isnan(c) and not np.isnan(u) else 0.0 for c, u in zip(x_coef, x_upper)]
    
    fig.add_trace(go.Scatter(
        x=x_coef,
        y=y_labels,
        mode='markers',
        name='Coefficient Beta (95% CI)',
        error_x=dict(
            type='data',
            symmetric=False,
            array=error_plus,
            arrayminus=error_minus,
            color=STATMIND_THEME["colors"]["secondary"],
            thickness=2,
            width=6
        ),
        marker=dict(color=STATMIND_THEME["colors"]["secondary"], size=10, symbol='diamond')
    ))
    
    fig.add_vline(x=0.0, line_dash="dash", line_color=STATMIND_THEME["colors"]["error"], line_width=2, annotation_text="No Effect (Beta=0.0)")
    fig.update_xaxes(title_text="Regression Coefficient Beta")
    fig.update_yaxes(title_text="Predictor Variable")
    
    fig = apply_statmind_theme(fig, title=title, subtitle=subtitle or "Horizontal bars crossing 0.0 indicate non-significant predictors at alpha=0.05")
    return fig_to_dict(fig)


def plot_means_ci(
    data: pd.DataFrame,
    dep_var: str,
    group_var: str,
    title: str,
    subtitle: Optional[str] = None
) -> Dict[str, Any]:
    """Generate Group Means plot with exact 95% Confidence Interval error bars."""
    df_clean = data[[dep_var, group_var]].dropna()
    groups = sorted(df_clean[group_var].unique())
    
    means = []
    ci_err = []
    
    for grp in groups:
        sub = df_clean[df_clean[group_var] == grp][dep_var]
        n = len(sub)
        m = float(sub.mean())
        s = float(sub.std(ddof=1)) if n > 1 else 0.0
        
        if n > 1 and s > 0:
            se = s / np.sqrt(n)
            t_crit = stats.t.ppf(0.975, df=n - 1)
            err = float(t_crit * se)
        else:
            err = 0.0
            
        means.append(m)
        ci_err.append(err)
        
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=[str(g) for g in groups],
        y=means,
        mode='markers+lines',
        name='Group Mean (95% CI)',
        error_y=dict(
            type='data',
            array=ci_err,
            visible=True,
            color=STATMIND_THEME["colors"]["primary"],
            thickness=2.5,
            width=8
        ),
        marker=dict(color=STATMIND_THEME["colors"]["primary"], size=11, symbol='circle'),
        line=dict(color=STATMIND_THEME["colors"]["primary"], width=2, dash='dot')
    ))
    
    fig.update_xaxes(title_text=group_var)
    fig.update_yaxes(title_text=f"Mean {dep_var} (±95% CI)")
    
    fig = apply_statmind_theme(fig, title=title, subtitle=subtitle or "Error bars display exact 95% confidence intervals of the group mean")
    return fig_to_dict(fig)


def plot_correlation_matrix(
    corr_df: pd.DataFrame,
    pval_df: pd.DataFrame,
    title: str,
    subtitle: Optional[str] = None
) -> Dict[str, Any]:
    """Generate Correlation Matrix Heatmap with significance star annotations (*, **, ***)."""
    text_annotations = []
    for r_row, p_row in zip(corr_df.values, pval_df.values):
        row_text = []
        for r_val, p_val in zip(r_row, p_row):
            if np.isnan(r_val):
                row_text.append("")
                continue
            stars = ""
            if p_val < 0.001:
                stars = "***"
            elif p_val < 0.01:
                stars = "**"
            elif p_val < 0.05:
                stars = "*"
            row_text.append(f"{r_val:.2f}{stars}")
        text_annotations.append(row_text)
        
    fig = go.Figure(data=go.Heatmap(
        z=corr_df.values,
        x=corr_df.columns.astype(str),
        y=corr_df.index.astype(str),
        colorscale='RdBu_r',
        zmin=-1.0,
        zmax=1.0,
        zmid=0.0,
        text=text_annotations,
        texttemplate="%{text}",
        colorbar=dict(title="Pearson r")
    ))
    
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="")
    
    fig = apply_statmind_theme(fig, title=title, subtitle=subtitle or "Significance annotations: * p < 0.05, ** p < 0.01, *** p < 0.001")
    return fig_to_dict(fig)


def plot_roc_curve(
    actual_y: pd.Series,
    fitted_probs: pd.Series,
    title: str,
    subtitle: Optional[str] = None
) -> Dict[str, Any]:
    """Generate ROC Curve (TPR vs FPR) and Area Under the Curve (AUC) for classification diagnostics."""
    clean = pd.DataFrame({'y': actual_y, 'p': fitted_probs}).dropna()
    
    # Map binary actual_y to 0 and 1
    unique_y = sorted(clean['y'].unique())
    if len(unique_y) != 2:
        # Fallback if not binary
        fpr = [0.0, 1.0]
        tpr = [0.0, 1.0]
        auc_score = 0.5
    else:
        y_bin = (clean['y'] == unique_y[1]).astype(int)
        
        try:
            from sklearn.metrics import roc_curve, roc_auc_score
            fpr, tpr, _ = roc_curve(y_bin, clean['p'])
            auc_score = float(roc_auc_score(y_bin, clean['p']))
            fpr = fpr.tolist()
            tpr = tpr.tolist()
        except ImportError:
            # Clean manual threshold sweep fallback
            thresholds = np.linspace(1.0, 0.0, 101)
            fpr = []
            tpr = []
            pos_total = sum(y_bin == 1)
            neg_total = sum(y_bin == 0)
            for thresh in thresholds:
                preds = (clean['p'] >= thresh).astype(int)
                tp = sum((preds == 1) & (y_bin == 1))
                fp = sum((preds == 1) & (y_bin == 0))
                tpr.append(tp / pos_total if pos_total > 0 else 0.0)
                fpr.append(fp / neg_total if neg_total > 0 else 0.0)
            # Trapezoidal AUC calculation
            auc_score = float(np.trapz(tpr, fpr))
            
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=fpr,
        y=tpr,
        mode='lines',
        name=f"ROC Curve (AUC = {auc_score:.3f})",
        line=dict(color=STATMIND_THEME["colors"]["primary"], width=3)
    ))
    
    # Random guess diagonal line
    fig.add_trace(go.Scatter(
        x=[0, 1],
        y=[0, 1],
        mode='lines',
        name="Random Guess (AUC = 0.500)",
        line=dict(color=STATMIND_THEME["colors"]["neutral"], width=2, dash='dash')
    ))
    
    fig.update_xaxes(title_text="False Positive Rate (1 - Specificity)", range=[-0.02, 1.02])
    fig.update_yaxes(title_text="True Positive Rate (Sensitivity)", range=[-0.02, 1.02])
    
    fig = apply_statmind_theme(fig, title=title, subtitle=subtitle or f"Overall Classification Discriminative Power: AUC = {auc_score:.3f}")
    return fig_to_dict(fig)
