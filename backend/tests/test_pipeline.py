import pandas as pd
import pytest
from backend.app.services.chat.parser import NaturalLanguageIntentParser
from backend.app.services.analysis.engine import AnalysisEngine
from backend.app.core.exceptions import StatisticalViolationException, AnalysisFailedException


def test_intent_to_engine_pipeline():
    """Verify that a natural language query maps to a method and successfully executes in the engine."""
    df = pd.DataFrame({
        "salary": [50000, 55000, 60000, 65000, 70000, 52000, 58000, 62000],
        "gender": ["Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female"]
    })
    columns_metadata = [
        {"name": "salary", "type": "continuous"},
        {"name": "gender", "type": "categorical"}
    ]

    query = "Is there a significant difference in salary between male and female employees?"
    recommendation = NaturalLanguageIntentParser.parse_query(query, columns_metadata)

    assert recommendation.method_id == "ttest_independent"
    assert recommendation.mapped_variables["dependent"] == "salary"
    assert recommendation.mapped_variables["grouping"] == "gender"

    # Execute via engine
    result = AnalysisEngine.execute_analysis(
        method_id=recommendation.method_id,
        data=df,
        variables=recommendation.mapped_variables
    )

    assert result.method_name == "Independent Samples T-Test"
    assert result.sample_size == 8
    assert result.r_code is not None
    assert result.python_code is not None


def test_engine_validation_error():
    """Verify that passing invalid variables raises StatisticalViolationException."""
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    with pytest.raises(StatisticalViolationException) as exc_info:
        AnalysisEngine.execute_analysis(
            method_id="ttest_independent",
            data=df,
            variables={"dependent": "NonExistentColumn", "grouping": "B"}
        )
    assert "Variable 'NonExistentColumn' not found" in exc_info.value.message
