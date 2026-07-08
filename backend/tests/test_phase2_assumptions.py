import pytest
import pandas as pd
import numpy as np
from backend.app.services.assumptions import tests as assumption_tests
from backend.app.services.assumptions.checker import AssumptionChecker


def test_binary_outcome_check_passed():
    s = pd.Series([0, 1, 0, 1, 1, 0])
    passed, u_count, _, details = assumption_tests.test_binary_outcome(s)
    assert passed is True
    assert u_count == 2.0


def test_binary_outcome_check_failed():
    s = pd.Series([0, 1, 2, 0])
    passed, u_count, _, details = assumption_tests.test_binary_outcome(s)
    assert passed is False
    assert u_count == 3.0


def test_residuals_normality_passed():
    np.random.seed(42)
    # Generate linear data with normal noise
    x = np.linspace(0, 10, 50)
    y = pd.Series(2 * x + np.random.normal(0, 0.5, 50))
    X = pd.DataFrame({"x": x})
    passed, stat, p, details = assumption_tests.test_residuals_normality(y, X)
    assert passed is True
    assert p >= 0.05


def test_residuals_normality_failed():
    np.random.seed(42)
    # Generate extreme exponential noise to violate normality of residuals
    x = np.linspace(0, 10, 50)
    y = pd.Series(2 * x + np.random.exponential(10.0, 50))
    X = pd.DataFrame({"x": x})
    passed, stat, p, details = assumption_tests.test_residuals_normality(y, X)
    assert passed is False
    assert p < 0.05


def test_vif_multicollinearity_passed():
    np.random.seed(42)
    x1 = np.random.normal(0, 1, 50)
    x2 = np.random.normal(5, 2, 50)  # Independent of x1
    X = pd.DataFrame({"x1": x1, "x2": x2})
    passed, max_vif, _, details = assumption_tests.test_vif_multicollinearity(X)
    assert passed is True
    assert max_vif < 10.0


def test_vif_multicollinearity_failed():
    np.random.seed(42)
    x1 = np.random.normal(0, 1, 50)
    x2 = x1 * 0.99 + np.random.normal(0, 0.001, 50)  # Highly collinear
    X = pd.DataFrame({"x1": x1, "x2": x2})
    passed, max_vif, _, details = assumption_tests.test_vif_multicollinearity(X)
    assert passed is False
    assert max_vif >= 10.0


def test_checker_with_list_independent():
    np.random.seed(42)
    df = pd.DataFrame({
        "y": np.random.normal(10, 2, 40),
        "x1": np.random.normal(1, 1, 40),
        "x2": np.random.normal(2, 1, 40)
    })
    results = AssumptionChecker.check_all("regression_linear_multiple", df, {"dependent": "y", "independent": ["x1", "x2"]})
    assert len(results) > 0
    assert any(r.assumption_name == "multicollinearity" for r in results)
