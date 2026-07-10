from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.services.chat.parser import NaturalLanguageIntentParser, IntentRecommendation
from backend.app.services.chat.intent import ChatConsultantService
from backend.app.services.session.manager import session_manager

router = APIRouter()


class RecommendRequest(BaseModel):
    query: str = Field(..., description="Natural language question e.g., 'Compare salary across genders'")
    dataset_id: Optional[str] = Field(None, description="ID of active dataset in session store")
    columns_metadata: Optional[List[Dict[str, Any]]] = Field(None, description="Columns metadata list")


class ConsultRequest(BaseModel):
    message: str = Field(default="", description="User follow-up message or question")
    user_message: Optional[str] = Field(None, description="Alternative message alias")
    dataset_id: Optional[str] = None
    history: List[Dict[str, Any]] = Field(default_factory=list, description="Recent conversation history")
    current_analysis: Optional[Dict[str, Any]] = Field(None, description="Active analysis results dictionary if applicable")
    recent_analysis: Optional[Dict[str, Any]] = Field(None, description="Most recent analysis summary")
    dataset_info: Optional[Dict[str, Any]] = Field(None, description="Dataset summary info e.g. name, rows, cols")
    variable_registry: Optional[List[Dict[str, Any]]] = Field(None, description="Available variables and inferred types")
    context: Optional[Dict[str, Any]] = Field(None, description="Frontend context envelope")


@router.post("/recommend", status_code=200)
async def recommend_method(request: RecommendRequest):
    """Recommend the optimal statistical method and variable mappings from a natural language query."""
    columns_meta = []
    if request.dataset_id:
        try:
            profile, _ = session_manager.get_dataset(request.dataset_id)
            columns_meta = [
                {"name": col.name, "type": col.detected_type.value}
                for col in profile.variables
            ]
        except Exception:
            pass
            
    if not columns_meta and request.columns_metadata:
        columns_meta = [
            {
                "name": col.get("name", ""),
                "type": col.get("data_type") or col.get("type") or col.get("detected_type") or "continuous",
                "n_unique": col.get("unique_values", col.get("n_unique", 0))
            }
            for col in request.columns_metadata
        ]
        
    recommendation = NaturalLanguageIntentParser.parse_query(request.query, columns_meta)
    rec_dict = recommendation.model_dump()
    return {
        "recommendation": rec_dict,
        **rec_dict,
        "message": f"Recommended {recommendation.method_name} with {int(recommendation.confidence * 100)}% confidence."
    }


@router.post("/consult", response_model=Dict[str, Any], status_code=200)
@router.post("/consult_ai", response_model=Dict[str, Any], status_code=200)
async def consult_assistant(request: ConsultRequest):
    """Bilingual statistical consultant assistant with stateful context injection."""
    ctx = request.context or {}
    dataset_id = request.dataset_id or ctx.get("dataset_id")
    columns_meta = ctx.get("columns_metadata") or []
    
    if not columns_meta and dataset_id:
        try:
            profile, _ = session_manager.get_dataset(dataset_id)
            columns_meta = [{"name": col.name, "type": col.detected_type.value} for col in profile.variables]
        except Exception:
            pass

    merged_context = {
        "columns_metadata": columns_meta,
        "current_analysis": request.current_analysis or ctx.get("current_analysis"),
        "recent_analysis": request.recent_analysis or ctx.get("recent_analysis"),
        "dataset_info": request.dataset_info or ctx.get("dataset_info"),
        "variable_registry": request.variable_registry or ctx.get("variable_registry") or columns_meta,
        "dataset_id": dataset_id,
    }
    
    active_message = (request.message or request.user_message or ctx.get("user_message") or ctx.get("message") or "").strip()
    
    response = ChatConsultantService.process_message(
        message=active_message,
        history=request.history,
        context=merged_context
    )
    return response
