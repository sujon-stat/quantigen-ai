from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from backend.app.models.variables import VariableType


class ColumnProfile(BaseModel):
    """Detailed profile of a single dataset column."""
    name: str
    detected_type: VariableType
    missing_count: int = 0
    missing_percentage: float = 0.0
    unique_values: int = 0
    sample_values: List[Any] = Field(default_factory=list)
    summary_stats: Dict[str, Any] = Field(default_factory=dict)


class VariableSummary(BaseModel):
    """Brief summary of a variable for AI prompt context blocks."""
    name: str
    type: VariableType
    role_suggestions: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class DatasetSummary(BaseModel):
    """Complete summary metadata of an uploaded dataset."""
    dataset_id: str
    name: str
    n_rows: int
    n_columns: int
    variables: List[ColumnProfile]
    missing_summary: str = Field(..., description="One-line summary of missingness")
