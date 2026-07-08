import numpy as np
import pandas as pd
import pytest
from backend.app.services.visualization import plotter


def test_plot_forest_odds_ratios():
    df = pd.DataFrame({
        "Odds_Ratio": [1.5, 0.8, 2.3],
        "CI_Lower": [1.1, 0.5, 1.4],
        "CI_Upper": [2.1, 1.2, 3.8]
    }, index=["Age", "Gender", "Treatment"])
    
    fig_dict = plotter.plot_forest_odds_ratios(df, title="Forest Plot OR")
    assert isinstance(fig_dict, dict)
    assert "data" in fig_dict and "layout" in fig_dict
    assert fig_dict["layout"]["xaxis"]["type"] == "log"
    # Ensure reference line at x=1.0 exists
    shapes = fig_dict["layout"].get("shapes", [])
    assert any(s.get("x0") == 1.0 and s.get("x1") == 1.0 for s in shapes)


def test_plot_forest_coefficients():
    df = pd.DataFrame({
        "coef": [0.45, -0.22],
        "CI_Lower": [0.12, -0.45],
        "CI_Upper": [0.78, 0.01]
    }, index=["Predictor1", "Predictor2"])
    
    fig_dict = plotter.plot_forest_coefficients(df, title="Forest Plot Coefs")
    assert isinstance(fig_dict, dict)
    shapes = fig_dict["layout"].get("shapes", [])
    assert any(s.get("x0") == 0.0 and s.get("x1") == 0.0 for s in shapes)


def test_plot_means_ci():
    np.random.seed(42)
    df = pd.DataFrame({
        "score": np.concatenate([np.random.normal(50, 5, 20), np.random.normal(60, 5, 20)]),
        "group": ["A"] * 20 + ["B"] * 20
    })
    
    fig_dict = plotter.plot_means_ci(df, dep_var="score", group_var="group", title="Means CI Plot")
    assert isinstance(fig_dict, dict)
    trace = fig_dict["data"][0]
    assert "error_y" in trace
    assert trace["error_y"]["visible"] is True
    assert len(trace["x"]) == 2


def test_plot_correlation_matrix():
    corr_df = pd.DataFrame([[1.0, 0.6], [0.6, 1.0]], columns=["X", "Y"], index=["X", "Y"])
    pval_df = pd.DataFrame([[0.0, 0.002], [0.002, 0.0]], columns=["X", "Y"], index=["X", "Y"])
    
    fig_dict = plotter.plot_correlation_matrix(corr_df, pval_df, title="Corr Heatmap")
    assert isinstance(fig_dict, dict)
    trace = fig_dict["data"][0]
    assert trace["type"] == "heatmap"
    assert "**" in trace["text"][0][1]  # 0.002 should have double star


def test_plot_roc_curve():
    actual = pd.Series([0, 0, 1, 1, 0, 1, 1, 0, 1, 0])
    probs = pd.Series([0.1, 0.2, 0.8, 0.9, 0.3, 0.7, 0.6, 0.4, 0.85, 0.15])
    
    fig_dict = plotter.plot_roc_curve(actual, probs, title="ROC Curve Test")
    assert isinstance(fig_dict, dict)
    assert len(fig_dict["data"]) == 2  # ROC trace + random guess trace
    assert "AUC =" in fig_dict["data"][0]["name"]
