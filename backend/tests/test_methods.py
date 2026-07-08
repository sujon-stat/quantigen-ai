import numpy as np
import pandas as pd
import pytest
from scipy import stats
from backend.app.services.statistics.descriptive import DescriptiveStatisticsMethod
from backend.app.services.statistics.ttest import IndependentSamplesTTestMethod
from backend.app.services.statistics.correlation import PearsonCorrelationMethod
from backend.app.services.statistics.chi_square import ChiSquareTestMethod
from backend.app.services.statistics.regression import SimpleLinearRegressionMethod


def test_descriptive_statistics_method():
    df = pd.DataFrame({
        "age": [25, 30, 35, 40, 45],
        "gender": ["M", "F", "F", "M", "M"]
    })
    method = DescriptiveStatisticsMethod()
    result = method.run(df, {"variables": ["age", "gender"]})
    
    assert result.sample_size == 5
    assert "age" in result.main_results["numeric_summaries"]
    assert result.main_results["numeric_summaries"]["age"]["mean"] == 35.0
    assert "gender" in result.main_results["categorical_summaries"]
    assert result.main_results["categorical_summaries"]["gender"]["top_category"] == "M"
    assert len(result.plots) > 0
    assert "library(tidyverse)" in result.r_code


def test_independent_ttest_method():
    np.random.seed(101)
    g1 = np.random.normal(50, 5, size=30)
    g2 = np.random.normal(55, 5, size=30)
    df = pd.DataFrame({
        "score": np.concatenate([g1, g2]),
        "treatment": ["Control"] * 30 + ["Treated"] * 30
    })

    method = IndependentSamplesTTestMethod()
    result = method.run(df, {"dependent": "score", "grouping": "treatment"})

    # Verify against scipy
    scipy_stat, scipy_p = stats.ttest_ind(g1, g2, equal_var=True)
    assert abs(result.main_results["t_statistic"] - scipy_stat) < 1e-4
    assert abs(result.main_results["p_value"] - scipy_p) < 1e-4
    assert abs(result.effect_sizes["cohens_d"]) != 0.0
    assert len(result.plots) == 3
    assert "t.test(" in result.r_code


def test_pearson_correlation_method():
    np.random.seed(102)
    x = np.linspace(1, 10, 20)
    y = 2 * x + np.random.normal(0, 0.5, size=20)
    df = pd.DataFrame({"X": x, "Y": y})

    method = PearsonCorrelationMethod()
    result = method.run(df, {"variables": ["X", "Y"]})

    scipy_r, scipy_p = stats.pearsonr(x, y)
    assert abs(result.main_results["pearson_r"] - scipy_r) < 1e-4
    assert abs(result.main_results["p_value"] - scipy_p) < 1e-4
    assert result.main_results["ci_95_lower"] < result.main_results["pearson_r"] < result.main_results["ci_95_upper"]
    assert len(result.plots) == 2


def test_chi_square_method():
    df = pd.DataFrame({
        "preference": ["Coffee"] * 40 + ["Tea"] * 10 + ["Coffee"] * 15 + ["Tea"] * 35,
        "region": ["North"] * 50 + ["South"] * 50
    })

    method = ChiSquareTestMethod()
    result = method.run(df, {"variables": ["preference", "region"]})

    crosstab = pd.crosstab(df["preference"], df["region"])
    scipy_chi2, scipy_p, dof, _ = stats.chi2_contingency(crosstab)

    assert abs(result.main_results["chi2_statistic"] - scipy_chi2) < 1e-4
    assert abs(result.main_results["p_value"] - scipy_p) < 1e-4
    assert result.main_results["degrees_of_freedom"] == 1
    assert result.effect_sizes["cramers_v"] > 0.0


def test_linear_regression_method():
    np.random.seed(103)
    x = np.linspace(0, 10, 25)
    y = 3.5 * x + 12.0 + np.random.normal(0, 1.0, size=25)
    df = pd.DataFrame({"X": x, "Y": y})

    method = SimpleLinearRegressionMethod()
    result = method.run(df, {"dependent": "Y", "independent": "X"}, options={"robust_se": False})

    slope, intercept, r_val, p_val, std_err = stats.linregress(x, y)
    assert abs(result.main_results["coefficients"]["slope"]["estimate"] - slope) < 1e-4
    assert abs(result.main_results["coefficients"]["intercept"]["estimate"] - intercept) < 1e-4
    assert abs(result.main_results["r_squared"] - (r_val ** 2)) < 1e-4
    assert len(result.plots) == 2
