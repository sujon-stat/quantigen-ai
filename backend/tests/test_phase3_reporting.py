import pytest
from backend.app.services.statistics.base import MethodResult
from backend.app.services.analysis.reporting import APAReportingService


def test_apa_reporting_independent_ttest():
    res = MethodResult(
        method_id="ttest_independent",
        method_name="Independent Samples T-Test",
        method_family="Group Comparisons",
        description="test",
        variables_used={"dependent": "score", "grouping": "treatment"},
        sample_size=60,
        python_code="",
        r_code="",
        interpretation="",
        main_results={
            "t_statistic": -3.26,
            "degrees_of_freedom": 58.0,
            "p_value": 0.002
        },
        effect_sizes={
            "cohens_d": -0.84,
            "d_ci_lower": -1.37,
            "d_ci_upper": -0.31
        }
    )
    citation = APAReportingService.generate_apa_citation(res)
    assert "t(58.00) = -3.26" in citation
    assert "p = .002" in citation
    assert "Cohen's d = -0.84" in citation
    assert "score across treatment" in citation


def test_apa_reporting_oneway_anova():
    res = MethodResult(
        method_id="anova_oneway",
        method_name="One-Way ANOVA",
        method_family="Group Comparisons",
        description="test",
        variables_used={"dependent": "salary", "grouping": "department"},
        sample_size=120,
        python_code="",
        r_code="",
        interpretation="",
        main_results={
            "f_statistic": 14.32,
            "df_between": 2,
            "df_within": 117,
            "p_value": 0.00004
        },
        effect_sizes={
            "eta_squared": 0.33
        }
    )
    citation = APAReportingService.generate_apa_citation(res)
    assert "F(2, 117) = 14.32" in citation
    assert "p < .001" in citation
    assert "\u03b7\u00b2 = 0.33" in citation


def test_apa_reporting_logistic_regression():
    res = MethodResult(
        method_id="binary_logistic_regression",
        method_name="Binary Logistic Regression",
        method_family="Regression Models",
        description="test",
        variables_used={"dependent": "admitted", "independent": ["gpa", "gre"]},
        sample_size=400,
        python_code="",
        r_code="",
        interpretation="",
        main_results={
            "likelihood_ratio_chi2": 41.46,
            "likelihood_ratio_p_value": 0.0001,
            "dof_model": 2.0,
            "mcfadden_pseudo_r_squared": 0.18
        }
    )
    citation = APAReportingService.generate_apa_citation(res)
    assert "\u03c7\u00b2(2) = 41.46" in citation
    assert "McFadden's R\u00b2 = 0.18" in citation
