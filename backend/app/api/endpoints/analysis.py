from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.models.analysis import AnalysisRequest, AnalysisResponse, MethodResult
from backend.app.models.assumptions import AssumptionResult, Severity
from backend.app.services.session.manager import session_manager
from backend.app.services.analysis.engine import AnalysisEngine
from backend.app.services.assumptions.checker import AssumptionChecker

router = APIRouter()


@router.post("/execute", response_model=AnalysisResponse, status_code=200)
async def execute_analysis(request: AnalysisRequest):
    """
    Execute a statistical method on a dataset stored in the session.
    First checks assumptions and returns 'assumptions_failed' if any critical assumption
    fails and override_assumptions=False.
    """
    profile, df = session_manager.get_dataset(request.dataset_id)
    
    # Execute analysis via orchestrator
    result = AnalysisEngine.execute_analysis(
        method_id=request.method_id,
        data=df,
        variables=request.variables,
        options=request.options
    )
    
    # Check severity of assumption outcomes
    has_critical_error = any(
        a.severity == Severity.ERROR and not a.passed
        for a in result.assumption_results
    )
    
    if has_critical_error and not request.override_assumptions:
        return AnalysisResponse(
            status="assumptions_failed",
            result=result,
            assumption_results=result.assumption_results,
            message="Critical statistical assumptions were violated. Please review the diagnostic warnings and remedies or check 'override_assumptions' if you still wish to proceed."
        )
        
    return AnalysisResponse(
        status="success",
        result=result,
        assumption_results=result.assumption_results,
        message=f"{result.method_name} completed successfully."
    )


@router.post("/assumptions/check", response_model=List[AssumptionResult], status_code=200)
async def check_assumptions(request: AnalysisRequest):
    """Pre-check assumption validity without running the full statistical method."""
    profile, df = session_manager.get_dataset(request.dataset_id)
    results = AssumptionChecker.check_all(
        method_id=request.method_id,
        data=df,
        variables=request.variables
    )
    return results
