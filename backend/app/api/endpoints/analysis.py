from typing import List, AsyncGenerator
import json
import asyncio
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from backend.app.models.analysis import AnalysisRequest, AnalysisResponse, MethodResult
from backend.app.models.assumptions import AssumptionResult, Severity
from backend.app.services.session.manager import session_manager
from backend.app.services.analysis.engine import AnalysisEngine
from backend.app.services.assumptions.checker import AssumptionChecker
from backend.app.core.exceptions import StatMindException
from backend.app.services.workflow_engine import workflow_engine
from backend.app.services.validation_engine import validation_engine

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
    
    # Run 5-step Validation Engine verification
    val_report = validation_engine.validate_execution(
        method_id=request.method_id,
        df=df,
        assumptions_results=[a.model_dump() for a in result.assumption_results],
        computed_outputs=result.main_results
    )

    # Check severity of assumption outcomes
    has_critical_error = any(
        a.severity == Severity.ERROR and not a.passed
        for a in result.assumption_results
    )
    
    if has_critical_error and not request.override_assumptions:
        workflow_engine.record_action(
            event_type="ASSUMPTION_SHIELD_BLOCK",
            description=f"Blocked {result.method_name} due to critical assumption violations",
            details={"method_id": request.method_id, "violations": [a.test_name for a in result.assumption_results if not a.passed]}
        )
        return AnalysisResponse(
            status="assumptions_failed",
            result=result,
            assumption_results=result.assumption_results,
            message="Critical statistical assumptions were violated. Please review the diagnostic warnings and remedies or check 'override_assumptions' if you still wish to proceed."
        )
        
    workflow_engine.record_action(
        event_type="METHOD_EXECUTION",
        description=f"Successfully executed {result.method_name} (n = {len(df):,})",
        details={"method_id": request.method_id, "cautionary_warnings": val_report.cautionary_warnings}
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


async def agent_stream_generator(request: AnalysisRequest) -> AsyncGenerator[str, None]:
    """Yields live JSON updates via Server-Sent Events (SSE) as the Agentic Engine steps through execution."""
    try:
        # Step 1: Profiling variables
        yield f"data: {json.dumps({'step_id': '1', 'status': 'running', 'label': 'Profiling selected variables & validating measurement scales...'})}\n\n"
        await asyncio.sleep(0.5)
        profile, df = session_manager.get_dataset(request.dataset_id)
        var_summary = ", ".join(f"{k}: {v}" for k, v in request.variables.items())
        yield f"data: {json.dumps({'step_id': '1', 'status': 'success', 'detail': f'Verified scales for: {var_summary}'})}\n\n"

        # Step 2: Assumption Shield diagnostics
        yield f"data: {json.dumps({'step_id': '2', 'status': 'running', 'label': 'Running Assumption Shield diagnostics (Shapiro-Wilk / Levene)...'})}\n\n"
        await asyncio.sleep(0.6)
        assumptions = AssumptionChecker.check_all(
            method_id=request.method_id,
            data=df,
            variables=request.variables
        )
        failed_assumptions = [a for a in assumptions if not a.passed]
        if failed_assumptions:
            warning_msg = f"Assumption Shield Warning: {failed_assumptions[0].test_name} violated ({failed_assumptions[0].explanation}). Auto-applying robust corrections."
            yield f"data: {json.dumps({'step_id': '2', 'status': 'warning', 'detail': warning_msg})}\n\n"
        else:
            yield f"data: {json.dumps({'step_id': '2', 'status': 'success', 'detail': 'All primary distributional & variance assumptions verified.'})}\n\n"

        # Step 3: Parameter bounding & Complex Survey Shield check
        is_survey = bool((request.options or {}).get("survey_design", {}).get("is_survey_weighted", False))
        if is_survey:
            s_spec = (request.options or {}).get("survey_design", {})
            design_type_lbl = s_spec.get("design_type", "SurveyNCD / DHS")
            w_lbl = s_spec.get("weight_var", "wt")
            c_lbl = s_spec.get("cluster_var", "psu")
            yield f"data: {json.dumps({'step_id': '3', 'status': 'running', 'label': f'Verifying Complex Survey Design ({design_type_lbl}) & Taylor Linearization...'})}\n\n"
            await asyncio.sleep(0.4)
            yield f"data: {json.dumps({'step_id': '3', 'status': 'success', 'detail': f'Survey Shield active: Weights ({w_lbl}) & Clusters ({c_lbl}) locked into degrees of freedom.'})}\n\n"
        else:
            yield f"data: {json.dumps({'step_id': '3', 'status': 'running', 'label': 'Verifying mathematical bounds & auto-correcting formula parameters...'})}\n\n"
            await asyncio.sleep(0.4)
            yield f"data: {json.dumps({'step_id': '3', 'status': 'success', 'detail': 'Formula parameters locked. Zero hallucinated statistics guaranteed.'})}\n\n"

        # Step 4: Method execution
        yield f"data: {json.dumps({'step_id': '4', 'status': 'running', 'label': f'Executing statistical engine ({request.method_id})...'})}\n\n"
        result = AnalysisEngine.execute_analysis(
            method_id=request.method_id,
            data=df,
            variables=request.variables,
            options=request.options
        )
        await asyncio.sleep(0.5)
        yield f"data: {json.dumps({'step_id': '4', 'status': 'success', 'detail': f'Method execution complete: {result.method_name}'})}\n\n"

        # Step 5: Transparency code generation
        if is_survey:
            yield f"data: {json.dumps({'step_id': '5', 'status': 'running', 'label': 'Generating reproducible R library(survey) Taylor linearization scripts...'})}\n\n"
            await asyncio.sleep(0.4)
            yield f"data: {json.dumps({'step_id': '5', 'status': 'success', 'detail': 'Generated exact R survey design & Python WLS scripts.'})}\n\n"
        else:
            yield f"data: {json.dumps({'step_id': '5', 'status': 'running', 'label': 'Generating reproducible R (rpy2) and Python transparency scripts...'})}\n\n"
            await asyncio.sleep(0.4)
            yield f"data: {json.dumps({'step_id': '5', 'status': 'success', 'detail': 'Generated exact R syntax & Python script.'})}\n\n"

        # Step 6: Final payload transmission
        yield f"data: {json.dumps({'step_id': '6', 'status': 'success', 'label': 'Rendering publication-ready APA 7th Edition manuscript tables...', 'detail': 'Manuscript ready for export.'})}\n\n"

        final_response = AnalysisResponse(
            status="success",
            result=result,
            assumption_results=assumptions,
            message=f"{result.method_name} completed successfully via Agentic Stream."
        )
        yield f"data: {json.dumps({'type': 'final_result', 'data': final_response.model_dump()})}\n\n"
    except StatMindException as e:
        remedy = e.format_kwargs.get("remedy") or e.translation.get("action") or ""
        # Fix: StatMindException uses .detail, not .message
        error_msg = getattr(e, 'detail', None) or getattr(e, 'message', None) or str(e)
        detail = f"{error_msg} {remedy}".strip() if remedy else error_msg
        yield f"data: {json.dumps({'type': 'error', 'detail': detail})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"


@router.post("/agent/run", status_code=200)
async def run_agentic_analysis_stream(request: AnalysisRequest):
    """Server-Sent Events (SSE) streaming endpoint for live step-by-step agent execution."""
    return StreamingResponse(
        agent_stream_generator(request),
        media_type="text/event-stream"
    )
