import numpy as np
import pandas as pd
import pytest
from backend.app.models.assumptions import Severity
from backend.app.services.assumptions.checker import AssumptionChecker
from backend.app.services.assumptions import tests as assumption_tests


def test_shapiro_wilk_normal_data():
    """Test Shapiro-Wilk normality on synthetic normal data."""
    np.random.seed(42)
    normal_data = pd.Series(np.random.normal(loc=50.0, scale=10.0, size=50))
    passed, stat, p_val, details = assumption_tests.test_shapiro_wilk(normal_data)
    assert passed is True
    assert p_val > 0.05
    assert stat > 0.95


def test_shapiro_wilk_skewed_data():
    """Test Shapiro-Wilk normality on synthetic skewed (exponential) data."""
    np.random.seed(42)
    skewed_data = pd.Series(np.random.exponential(scale=2.0, size=50))
    passed, stat, p_val, details = assumption_tests.test_shapiro_wilk(skewed_data)
    assert passed is False
    assert p_val < 0.05


def test_levene_homogeneity():
    """Test Levene's test for equal variances across groups."""
    np.random.seed(42)
    g1 = pd.Series(np.random.normal(0, 1.0, size=40))
    g2 = pd.Series(np.random.normal(0, 1.0, size=40))
    g3_unequal = pd.Series(np.random.normal(0, 5.0, size=40))

    passed_equal, stat_eq, p_eq, _ = assumption_tests.test_levene_homogeneity([g1, g2])
    assert passed_equal is True
    assert p_eq > 0.05

    passed_unequal, stat_uneq, p_uneq, _ = assumption_tests.test_levene_homogeneity([g1, g3_unequal])
    assert passed_unequal is False
    assert p_uneq < 0.05


def test_assumption_checker_clt_adjustment():
    """Verify that normality failure gets downgraded from ERROR to WARNING when sample size > 30 (CLT rule)."""
    np.random.seed(42)
    # Generate skewed data with n = 60 per group
    df = pd.DataFrame({
        "score": np.concatenate([np.random.exponential(1.0, size=60), np.random.exponential(1.0, size=60)]),
        "group": ["A"] * 60 + ["B"] * 60
    })

    results = AssumptionChecker.check_all(
        method_id="ttest_independent",
        data=df,
        variables={"dependent": "score", "grouping": "group"}
    )

    normality_res = next((r for r in results if r.assumption_name == "normality"), None)
    assert normality_res is not None
    assert normality_res.passed is False
    assert normality_res.severity == Severity.WARNING
    assert normality_res.details.get("clt_applied") is True
