from fastapi import APIRouter
from typing import List, Dict, Any
from backend.app.services.data_engine import DataParserRegistry
from backend.app.services.statistics import MethodRegistry
from backend.app.services.workflow_engine import workflow_engine
from backend.app.services.plugin_engine import plugin_manager

router = APIRouter()


@router.get("/parsers", response_model=List[Dict[str, Any]], status_code=200)
async def list_data_parsers():
    """
    Return all registered Data Import Engine parsers (`BaseDataParser`).
    Supports dynamic discovery across CSV, Excel, SPSS, Stata, SAS, Parquet, RData, JSON, REDCap/DHS.
    """
    return DataParserRegistry.list_parsers()


@router.get("/methods-manifest", response_model=List[Dict[str, Any]], status_code=200)
async def list_methods_manifest():
    """
    Return complete metadata manifest for all registered Statistical Engine methods (`BaseStatisticalMethod`).
    Includes assumption dependencies, required roles, min sample sizes, and output definitions.
    """
    manifests = []
    for mid, instance in MethodRegistry._methods.items():
        manifests.append({
            "method_id": mid,
            "name": getattr(instance, "method_name", mid),
            "description": getattr(instance, "description", ""),
            "required_variables": getattr(instance, "required_variables", {}),
            "assumptions": [a.model_dump() for a in getattr(instance, "assumptions", []) if hasattr(a, "model_dump")],
            "family": getattr(instance, "method_family", "")
        })
    return manifests


@router.get("/audit-trail", response_model=List[Dict[str, Any]], status_code=200)
async def get_workflow_audit_trail():
    """
    Retrieve chronological audit trail (`Workflow Engine`) tracking all user steps,
    dataset transformations, assumption validations, and report compilations.
    """
    return workflow_engine.get_audit_trail()


@router.get("/plugins", response_model=List[Dict[str, Any]], status_code=200)
async def list_plugins():
    """
    Retrieve all loaded third-party and institutional plugins (`Plugin Engine`).
    """
    return plugin_manager.list_plugins()
