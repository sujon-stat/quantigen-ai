from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app.services.chat.parser import NaturalLanguageIntentParser, IntentRecommendation
from backend.app.services.chat.intent import ChatConsultantService
from backend.app.services.session.manager import session_manager

router = APIRouter()


class RecommendRequest(BaseModel):
    query: str = Field(..., description="Natural language question e.g., 'Compare salary across genders'")
    dataset_id: str = Field(..., description="ID of active dataset in session store")


class ConsultRequest(BaseModel):
    message: str = Field(..., description="User follow-up message or question")
    dataset_id: Optional[str] = None
    history: List[Dict[str, str]] = Field(default_factory=list, description="Recent conversation history")
    current_analysis: Optional[Dict[str, Any]] = Field(None, description="Active analysis results dictionary if applicable")


@router.post("/recommend", response_model=IntentRecommendation, status_code=200)
async def recommend_method(request: RecommendRequest):
    """Recommend the optimal statistical method and variable mappings from a natural language query."""
    profile, _ = session_manager.get_dataset(request.dataset_id)
    
    columns_meta = [
        {"name": col.name, "type": col.detected_type.value}
        for col in profile.variables
    ]
    
    recommendation = NaturalLanguageIntentParser.parse_query(request.query, columns_meta)
    return recommendation


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
