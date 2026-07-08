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
    message: str = Field(..., description="User follow-up message or question")
    dataset_id: Optional[str] = None
    history: List[Dict[str, str]] = Field(default_factory=list, description="Recent conversation history")
    current_analysis: Optional[Dict[str, Any]] = Field(None, description="Active analysis results dictionary if applicable")


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
    return {
        "recommendation": recommendation.model_dump(),
        "message": f"Recommended {recommendation.method_name} with {int(recommendation.confidence * 100)}% confidence."
    }


@router.post("/consult", response_model=Dict[str, Any], status_code=200)
async def consult_assistant(request: ConsultRequest):
    """Bilingual statistical consultant assistant for answering questions about p-values, assumptions, or alternative methods."""
    columns_meta = []
    if request.dataset_id:
        try:
            profile, _ = session_manager.get_dataset(request.dataset_id)
            columns_meta = [{"name": col.name, "type": col.detected_type.value} for col in profile.variables]
        except Exception:
            pass
            
    context = {
        "columns_metadata": columns_meta,
        "current_analysis": request.current_analysis
    }
    
    response = ChatConsultantService.process_message(
        message=request.message,
        history=request.history,
        context=context
    )
    return response
