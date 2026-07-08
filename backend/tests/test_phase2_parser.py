import pytest
from backend.app.services.chat.parser import NaturalLanguageIntentParser


def test_parse_query_anova():
    metadata = [
        {"name": "salary", "type": "continuous"},
        {"name": "department", "type": "categorical", "n_unique": 4}
    ]
    query = "Compare salary across the different department groups using ANOVA"
    rec = NaturalLanguageIntentParser.parse_query(query, metadata)
    assert rec.method_id == "anova_oneway"
    assert rec.mapped_variables["dependent"] == "salary"
    assert rec.mapped_variables["grouping"] == "department"


def test_parse_query_mann_whitney():
    metadata = [
        {"name": "pain_score", "type": "ordinal"},
        {"name": "drug_group", "type": "categorical", "n_unique": 2}
    ]
    query = "Run a Mann-Whitney U test between pain_score and drug_group"
    rec = NaturalLanguageIntentParser.parse_query(query, metadata)
    assert rec.method_id == "mann_whitney_u"


def test_parse_query_kruskal():
    metadata = [
        {"name": "recovery_days", "type": "continuous"},
        {"name": "hospital_site", "type": "categorical", "n_unique": 5}
    ]
    query = "Check differences in recovery_days across hospital_site using Kruskal-Wallis"
    rec = NaturalLanguageIntentParser.parse_query(query, metadata)
    assert rec.method_id == "kruskal_wallis"


def test_parse_query_multiple_regression():
    metadata = [
        {"name": "blood_pressure", "type": "continuous"},
        {"name": "age", "type": "continuous"},
        {"name": "weight", "type": "continuous"}
    ]
    query = "Predict blood_pressure from age and weight using multiple regression"
    rec = NaturalLanguageIntentParser.parse_query(query, metadata)
    assert rec.method_id == "regression_linear_multiple"
    assert rec.mapped_variables["dependent"] == "blood_pressure"
    assert set(rec.mapped_variables["independent"]) == {"age", "weight"}


def test_parse_query_binary_logistic():
    metadata = [
        {"name": "readmitted", "type": "binary", "n_unique": 2},
        {"name": "age", "type": "continuous"},
        {"name": "glucose", "type": "continuous"}
    ]
    query = "Conduct logistic regression to predict the binary outcome readmitted from age and glucose"
    rec = NaturalLanguageIntentParser.parse_query(query, metadata)
    assert rec.method_id == "regression_logistic"
    assert rec.mapped_variables["dependent"] == "readmitted"
    assert set(rec.mapped_variables["independent"]) == {"age", "glucose"}
