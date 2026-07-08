from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.services.statistics.registry import MethodRegistry
from backend.app.services.assumptions.rules import get_rules_for_method
from backend.app.services.statistics import bootstrap_registry

# Ensure registry is initialized
bootstrap_registry()

router = APIRouter()


@router.get("", response_model=List[Dict[str, Any]], status_code=200)
async def list_methods(family: Optional[str] = Query(None, description="Filter methods by family (e.g. 'parametric', 'descriptive')")):
    """List all available statistical methods registered in StatMind AI."""
    methods = MethodRegistry.list_all()
    if family:
        methods = [m for m in methods if m.get("family", "").lower() == family.lower()]
    return methods


@router.get("/{method_id}", response_model=Dict[str, Any], status_code=200)
async def get_method_details(method_id: str):
    """Retrieve complete metadata and assumption rules for a specific statistical method."""
    method = MethodRegistry.get(method_id)
    if not method:
        raise HTTPException(status_code=404, detail=f"Method '{method_id}' is not registered in StatMind AI.")
        
    rules = get_rules_for_method(method_id)
    rules_metadata = [
        {
            "name": r.name,
            "description": r.description,
            "test_name": r.test_name,
            "threshold": str(r.threshold) if r.threshold is not None else None,
            "severity": r.severity.value,
            "remedy": r.remedy
        }
        for r in rules
    ]
    
    return {
        "method_id": method.method_id,
        "name": method.method_name,
        "family": method.method_family,
        "description": method.description,
        "required_variables": method.required_variables,
        "optional_variables": method.optional_variables,
        "assumptions_checked": rules_metadata
    }
