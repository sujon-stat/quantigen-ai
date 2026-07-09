from pydantic import BaseModel, Field, model_validator
from typing import Any, Dict, List, Optional
from backend.app.models.variables import VariableType


class ColumnProfile(BaseModel):
    """Detailed profile of a single dataset column."""
    name: str
    detected_type: VariableType
    data_type: Optional[str] = None
    role: Optional[str] = None
    missing_count: int = 0
    missing_percentage: float = 0.0
    unique_values: int = 0
    sample_values: List[Any] = Field(default_factory=list)
    summary_stats: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_frontend_fields(self) -> "ColumnProfile":
        if not self.data_type:
            self.data_type = self.detected_type.value if hasattr(self.detected_type, "value") else str(self.detected_type)
        if not self.role:
            dt_str = self.data_type.lower() if self.data_type else ""
            if dt_str in ["continuous", "count", "ordinal"]:
                self.role = "continuous"
            elif dt_str in ["binary"]:
                self.role = "binary"
            else:
                self.role = "categorical"
        if isinstance(self.summary_stats, dict):
            if "top_categories" in self.summary_stats and "categories" not in self.summary_stats:
                self.summary_stats["categories"] = self.summary_stats["top_categories"]
            elif "categories" in self.summary_stats and "top_categories" not in self.summary_stats:
                self.summary_stats["top_categories"] = self.summary_stats["categories"]
        return self


class VariableSummary(BaseModel):
    """Brief summary of a variable for AI prompt context blocks."""
    name: str
    type: VariableType
    role_suggestions: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class SurveyDesignSpec(BaseModel):
    """Complex survey sampling design specification for DHS / MICS / STEPS / SurveyNCD weighted analysis."""
    is_survey_weighted: bool = False
    design_type: Optional[str] = "Complex Survey (Taylor Linearization)"
    weight_var: Optional[str] = None
    cluster_var: Optional[str] = None
    strata_var: Optional[str] = None
    nest: bool = True
    template_name: Optional[str] = None


class DatasetSummary(BaseModel):
    """Complete summary metadata of an uploaded dataset."""
    dataset_id: str
    name: str
    filename: Optional[str] = None
    n_rows: int
    total_rows: Optional[int] = None
    n_columns: int
    total_columns: Optional[int] = None
    variables: List[ColumnProfile]
    columns: Optional[List[ColumnProfile]] = None
    preview_data: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    missing_values_total: Optional[int] = None
    missing_summary: str = Field(..., description="One-line summary of missingness")
    survey_design: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Active survey weighting/cluster/strata design specification")

    @model_validator(mode="after")
    def sync_frontend_fields(self) -> "DatasetSummary":
        if not self.filename:
            self.filename = self.name
        if self.total_rows is None:
            self.total_rows = self.n_rows
        if self.total_columns is None:
            self.total_columns = self.n_columns
        if not self.columns:
            self.columns = self.variables
        if not self.variables and self.columns:
            self.variables = self.columns
        if self.missing_values_total is None:
            self.missing_values_total = sum(v.missing_count for v in self.variables)
        return self

