import pytest
import pandas as pd
from backend.app.models.analysis import MethodResult
from backend.app.services.r_integration.validator import StatisticalValidator


def test_validate_precision_exact_match():
    res = MethodResult(
        method_id="test_method",
        method_name="Test Method",
        method_family="Test Family",
        description="Testing precision",
        variables_used={"dep": "y"},
        sample_size=100,
        main_results={"t_statistic": 2.345678, "p_value": 0.021234},
        effect_sizes={"cohens_d": 0.469135},
        python_code="# py",
        r_code="# r",
        interpretation="passed"
    )
    expected = {"t_statistic": 2.345678, "p_value": 0.021234, "cohens_d": 0.469135}
    passed, errors, details = StatisticalValidator.validate_precision(res, expected, tolerance=1e-6)
    assert passed is True
    assert len(errors) == 0
    assert all(details[k]["passed"] for k in expected)


def test_validate_precision_within_tolerance():
    res = MethodResult(
        method_id="test_method",
        method_name="Test Method",
        method_family="Test Family",
        description="Testing precision",
        variables_used={"dep": "y"},
        sample_size=100,
        main_results={"f_statistic": 15.0000001, "p_value": 0.00010002},
        python_code="# py",
        r_code="# r",
        interpretation="passed"
    )
    expected = {"f_statistic": 15.0, "p_value": 0.0001}
    passed, errors, details = StatisticalValidator.validate_precision(res, expected, tolerance=1e-4)
    assert passed is True
    assert len(errors) == 0


def test_validate_precision_failure_outside_tolerance():
    res = MethodResult(
        method_id="test_method",
        method_name="Test Method",
        method_family="Test Family",
        description="Testing precision",
        variables_used={"dep": "y"},
        sample_size=100,
        main_results={"t_statistic": 2.5, "p_value": 0.01},
        python_code="# py",
        r_code="# r",
        interpretation="passed"
    )
    expected = {"t_statistic": 2.8, "p_value": 0.005}
    passed, errors, details = StatisticalValidator.validate_precision(res, expected, tolerance=1e-6)
    assert passed is False
    assert len(errors) == 2


def test_generate_r_verification_script():
    res = MethodResult(
        method_id="anova_oneway",
        method_name="One-Way ANOVA",
        method_family="Group Comparisons",
        description="Testing R script gen",
        variables_used={"dependent": "score", "grouping": "group"},
        sample_size=60,
        main_results={"f_stat": 4.5},
        python_code="# py",
        r_code="model <- aov(score ~ group, data = data)\nsummary(model)",
        interpretation="passed"
    )
    script = StatisticalValidator.generate_r_verification_script(res, "C:/data/test.csv")
    assert "C:/data/test.csv" in script
    assert "model <- aov(score ~ group, data = data)" in script


def test_run_rscript_verification():
    df = pd.DataFrame({"score": [10, 12, 14, 20, 22, 24], "group": ["A", "A", "A", "B", "B", "B"]})
    res = MethodResult(
        method_id="ttest_independent",
        method_name="Independent T-Test",
        method_family="T-Tests",
        description="Testing harness",
        variables_used={"dependent": "score", "grouping": "group"},
        sample_size=6,
        main_results={"t_statistic": -5.0, "p_value": 0.005},
        python_code="# py",
        r_code="t.test(score ~ group, data = data)",
        interpretation="passed"
    )
    expected = {"t_statistic": -5.0, "p_value": 0.005}
    output = StatisticalValidator.run_rscript_verification(res, df, expected)
    assert output["python_precision_passed"] is True
    assert "rscript_verification" in output
