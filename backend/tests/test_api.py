import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


@pytest.fixture
def sample_dataset_id() -> str:
    """Upload a sample CSV and return the generated dataset_id."""
    csv_data = b"age,salary,gender\n25,50000,Male\n30,55000,Female\n35,62000,Male\n40,68000,Female\n45,75000,Male\n28,52000,Female\n33,60000,Male\n38,65000,Female\n"
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("sample.csv", csv_data, "text/csv")}
    )
    assert response.status_code == 201
    return response.json()["dataset_id"]


def test_health_check():
    """Verify system health endpoint returns 200 OK and active dataset count."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "active_datasets_count" in data


def test_upload_dataset():
    """Verify uploading a CSV dataset correctly profiles columns and data types."""
    csv_data = b"score,group\n85.5,Control\n90.0,Treatment\n78.2,Control\n88.1,Treatment\n"
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("experiment.csv", csv_data, "text/csv")}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["n_rows"] == 4
    assert data["n_columns"] == 2
    assert len(data["variables"]) == 2
    
    col_names = [v["name"] for v in data["variables"]]
    assert "score" in col_names
    assert "group" in col_names


def test_get_dataset_and_update_variable(sample_dataset_id: str):
    """Verify retrieving dataset profile + rows, then updating a variable type."""
    get_res = client.get(f"/api/v1/datasets/{sample_dataset_id}?limit=5")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert "profile" in get_data
    assert "preview_rows" in get_data
    assert len(get_data["preview_rows"]) == 5

    # Update 'gender' variable to binary
    patch_res = client.patch(
        f"/api/v1/datasets/{sample_dataset_id}/variables/gender",
        json={"detected_type": "binary"}
    )
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    gender_var = next((v for v in patch_data["variables"] if v["name"] == "gender"), None)
    assert gender_var is not None
    assert gender_var["detected_type"] == "binary"


def test_list_methods_and_details():
    """Verify discovering available statistical methods and reading their assumption rules."""
    list_res = client.get("/api/v1/methods")
    assert list_res.status_code == 200
    methods = list_res.json()
    assert len(methods) >= 5
    
    # Check details for ttest_independent
    details_res = client.get("/api/v1/methods/ttest_independent")
    assert details_res.status_code == 200
    details = details_res.json()
    assert details["method_id"] == "ttest_independent"
    assert "assumptions_checked" in details
    assert len(details["assumptions_checked"]) > 0


def test_execute_analysis_and_check_assumptions(sample_dataset_id: str):
    """Verify executing an independent t-test on uploaded session dataset."""
    payload = {
        "dataset_id": sample_dataset_id,
        "method_id": "ttest_independent",
        "variables": {"dependent": "salary", "grouping": "gender"},
        "options": {},
        "override_assumptions": True
    }
    
    # First test assumption pre-check endpoint
    check_res = client.post("/api/v1/analysis/assumptions/check", json=payload)
    assert check_res.status_code == 200
    assumptions = check_res.json()
    assert isinstance(assumptions, list)
    
    # Execute full analysis
    exec_res = client.post("/api/v1/analysis/execute", json=payload)
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "success"
    result = exec_data["result"]
    assert result["method_name"] == "Independent Samples T-Test"
    assert result["sample_size"] == 8
    assert len(result["plots"]) == 3
    assert "t.test(" in result["r_code"]
    assert "Interpretation" in result["interpretation"] or "findings" in result["interpretation"].lower()


def test_chat_recommend_and_consult(sample_dataset_id: str):
    """Verify natural language recommendation and conversational advice."""
    rec_res = client.post(
        "/api/v1/chat/recommend",
        json={"query": "Is there a significant difference in salary between males and females?", "dataset_id": sample_dataset_id}
    )
    assert rec_res.status_code == 200
    rec = rec_res.json()
    assert rec["method_id"] == "ttest_independent"
    assert rec["mapped_variables"]["dependent"] == "salary"
    assert rec["mapped_variables"]["grouping"] == "gender"
    
    # Consult assistant about p-value
    consult_res = client.post(
        "/api/v1/chat/consult",
        json={
            "message": "What does a p-value of 0.03 mean here?",
            "dataset_id": sample_dataset_id,
            "current_analysis": {"method_name": "Independent Samples T-Test", "main_results": {"p_value": 0.03}}
        }
    )
    assert consult_res.status_code == 200
    consult = consult_res.json()
    assert consult["response_type"] == "educational_explanation"
    assert "probability" in consult["message"].lower() or "null hypothesis" in consult["message"].lower()


def test_export_script_and_report():
    """Verify exporting reproducible R script and Markdown report."""
    script_res = client.post(
        "/api/v1/export/script",
        json={"code": "library(tidyverse)\nprint('Hello')", "language": "r", "filename": "test_script"}
    )
    assert script_res.status_code == 200
    assert "attachment; filename=\"test_script.R\"" in script_res.headers["content-disposition"]
    assert "library(tidyverse)" in script_res.text
    
    report_res = client.post(
        "/api/v1/export/report",
        json={
            "method_name": "Independent T-Test",
            "description": "Compares group means",
            "sample_size": 30,
            "interpretation": "Significant difference found.",
            "r_code": "t.test(Y ~ X)",
            "python_code": "scipy.stats.ttest_ind(g1, g2)",
            "format": "markdown"
        }
    )
    assert report_res.status_code == 200
    assert "# StatMind AI" in report_res.text
    assert "Significant difference found." in report_res.text


def test_exception_handler_structured_error(sample_dataset_id: str):
    """Verify that passing an invalid variable name returns structured 422 JSON error."""
    payload = {
        "dataset_id": sample_dataset_id,
        "method_id": "ttest_independent",
        "variables": {"dependent": "NonExistentColumn", "grouping": "gender"}
    }
    response = client.post("/api/v1/analysis/execute", json=payload)
    assert response.status_code == 422
    err_data = response.json()
    assert err_data["status"] == "error"
    assert err_data["error_code"] == "StatisticalViolation"
    assert err_data["level"] == "assumption_violation"
    assert "NonExistentColumn" in err_data["message"]
    assert "icon" in err_data
