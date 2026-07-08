import pytest
import numpy as np
import pandas as pd
from scipy import stats
from backend.app.services.statistics.registry import MethodRegistry
from backend.app.services.r_integration.validator import StatisticalValidator


def test_oneway_anova_standard_and_welch():
    np.random.seed(42)
    # Generate 3 groups
    g1 = np.random.normal(10, 2, 30)
    g2 = np.random.normal(14, 2, 30)
    g3 = np.random.normal(12, 2, 30)
    
    df = pd.DataFrame({
        "score": np.concatenate([g1, g2, g3]),
        "group": ["A"] * 30 + ["B"] * 30 + ["C"] * 30
    })
    
    method = MethodRegistry.get("anova_oneway")
    result = method.run(df, {"dependent": "score", "grouping": "group"}, {"equal_var": True})
    
    assert result.method_id == "anova_oneway"
    assert result.main_results["k_groups"] == 3
    assert result.main_results["f_statistic"] > 5.0
    assert result.main_results["p_value"] < 0.001
    assert result.effect_sizes["eta_squared"] > 0.1
    assert result.post_hoc_results is not None
    assert len(result.post_hoc_results["comparisons"]) == 3
    
    # Precision check against scipy f_oneway directly
    scipy_f, scipy_p = stats.f_oneway(g1, g2, g3)
    passed, errs, details = StatisticalValidator.validate_precision(
        result,
        {"f_statistic": float(scipy_f), "p_value": float(scipy_p)},
        tolerance=1e-6
    )
    assert passed is True, f"Precision mismatch: {errs}"


def test_mann_whitney_u_and_rank_biserial():
    np.random.seed(42)
    g1 = np.random.normal(50, 10, 25)
    g2 = np.random.normal(65, 10, 25)
    
    df = pd.DataFrame({
        "val": np.concatenate([g1, g2]),
        "treatment": ["Control"] * 25 + ["Treated"] * 25
    })
    
    method = MethodRegistry.get("mann_whitney_u")
    result = method.run(df, {"dependent": "val", "grouping": "treatment"})
    
    assert result.method_id == "mann_whitney_u"
    assert result.main_results["p_value"] < 0.05
    assert -1.0 <= result.effect_sizes["rank_biserial_r"] <= 1.0
    
    scipy_u, scipy_p = stats.mannwhitneyu(g1, g2, alternative='two-sided')
    passed, errs, _ = StatisticalValidator.validate_precision(
        result,
        {"u_statistic": float(scipy_u), "p_value": float(scipy_p)},
        tolerance=1e-6
    )
    assert passed is True


def test_kruskal_wallis_h_and_bonferroni():
    np.random.seed(42)
    g1 = np.random.exponential(2, 20)
    g2 = np.random.exponential(5, 20)
    g3 = np.random.exponential(3, 20)
    
    df = pd.DataFrame({
        "time": np.concatenate([g1, g2, g3]),
        "dept": ["X"] * 20 + ["Y"] * 20 + ["Z"] * 20
    })
    
    method = MethodRegistry.get("kruskal_wallis")
    result = method.run(df, {"dependent": "time", "grouping": "dept"})
    
    assert result.method_id == "kruskal_wallis"
    assert result.main_results["k_groups"] == 3
    assert 0.0 <= result.effect_sizes["epsilon_squared"] <= 1.0
    
    scipy_h, scipy_p = stats.kruskal(g1, g2, g3)
    passed, errs, _ = StatisticalValidator.validate_precision(
        result,
        {"h_statistic": float(scipy_h), "p_value": float(scipy_p)},
        tolerance=1e-6
    )
    assert passed is True


def test_multiple_linear_regression_vif_and_r2():
    np.random.seed(42)
    n = 60
    x1 = np.random.normal(10, 2, n)
    x2 = np.random.normal(5, 1, n)
    # y = 3 + 2*x1 - 1.5*x2 + noise
    y = 3 + 2 * x1 - 1.5 * x2 + np.random.normal(0, 0.5, n)
    
    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
    
    method = MethodRegistry.get("regression_linear_multiple")
    result = method.run(df, {"dependent": "y", "independent": ["x1", "x2"]})
    
    assert result.method_id == "regression_linear_multiple"
    assert result.main_results["r_squared"] > 0.8
    assert len(result.main_results["coefficients"]) == 3  # const, x1, x2
    assert "x1" in result.main_results["vif_diagnostics"]
    assert "x2" in result.main_results["vif_diagnostics"]


def test_binary_logistic_regression_odds_ratios():
    np.random.seed(42)
    n = 80
    x = np.random.normal(0, 1.5, n)
    # Logit probability p = 1 / (1 + exp(-(0.5 + 2*x)))
    prob = 1.0 / (1.0 + np.exp(-(0.5 + 2.0 * x)))
    y = np.where(np.random.uniform(0, 1, n) < prob, 1, 0)
    
    df = pd.DataFrame({"outcome": y, "biomarker": x})
    
    method = MethodRegistry.get("regression_logistic")
    result = method.run(df, {"dependent": "outcome", "independent": ["biomarker"]})
    
    assert result.method_id == "regression_logistic"
    assert 0.0 <= result.effect_sizes["mcfadden_pseudo_r2"] <= 1.0
    
    # Check that biomarker coefficient and Odds Ratio exist and make sense
    coefs = {c["variable"]: c for c in result.main_results["coefficients"]}
    assert "biomarker" in coefs
    assert coefs["biomarker"]["odds_ratio"] > 1.0  # Positive association
