import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.data_engine import DataParserRegistry
from backend.app.services.workflow_engine import workflow_engine
from backend.app.services.plugin_engine import plugin_manager
from backend.app.services.validation_engine import validation_engine

client = TestClient(app)


def test_data_parser_registry():
    """Verify that all 9 modular data parsers are registered and discoverable."""
    parsers = DataParserRegistry.list_parsers()
    parser_ids = [p["id"] for p in parsers]
    assert "csv" in parser_ids
    assert "excel" in parser_ids
    assert "json" in parser_ids
    assert "spss" in parser_ids
    assert "stata" in parser_ids
    assert "sas" in parser_ids
    assert "parquet" in parser_ids
    assert "rdata" in parser_ids
    assert "survey" in parser_ids
    assert len(parsers) >= 9


def test_registry_endpoints():
    """Verify clean REST exposure of modular engines via /api/v1/registry/."""
    # Test parsers endpoint
    res = client.get("/api/v1/registry/parsers")
    assert res.status_code == 200
    parsers_data = res.json()
    assert len(parsers_data) >= 9

    # Test methods manifest endpoint
    res = client.get("/api/v1/registry/methods-manifest")
    assert res.status_code == 200
    methods_data = res.json()
    assert len(methods_data) >= 10

    # Test workflow audit trail endpoint
    res = client.get("/api/v1/registry/audit-trail")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # Test plugins list endpoint
    res = client.get("/api/v1/registry/plugins")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_workflow_audit_recording():
    """Verify event recording in Workflow Engine."""
    workflow_engine.clear()
    workflow_engine.record_action("TEST_EVENT", "Unit test action description", details={"key": "value"})
    trail = workflow_engine.get_audit_trail()
    assert len(trail) == 1
    assert trail[0]["event_type"] == "TEST_EVENT"
    assert trail[0]["details"]["key"] == "value"
