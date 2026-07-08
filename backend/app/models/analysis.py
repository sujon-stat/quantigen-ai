from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional
from backend.app.models.assumptions import AssumptionResult


class MethodResult(BaseModel):
    """Complete result from a statistical method execution."""
    method_id: str = Field("", description="Unique method identifier e.g., 'anova_oneway'")
    method_name: str = Field(..., description="Full display name e.g., 'Independent Samples T-Test'")
    method_family: str = Field(..., description="Method family e.g., 'T-Tests', 'Regression'")
    description: str = Field(..., description="What this analysis does")
    variables_used: Dict[str, Any] = Field(..., description="Role to variable mapping e.g., {'dependent': 'salary', 'grouping': 'gender'}")
    sample_size: int = Field(..., description="Final sample size N after missing value exclusion")
    assumption_results: List[AssumptionResult] = Field(default_factory=list, description="Results of all assumption checks")
    main_results: Dict[str, Any] = Field(default_factory=dict, description="Test statistics, p-values, degrees of freedom")
    effect_sizes: Optional[Dict[str, Any]] = Field(None, description="Effect size calculations and confidence intervals")
    post_hoc_results: Optional[Dict[str, Any]] = Field(None, description="Post-hoc multiple comparisons if applicable")
    python_code: str = Field(..., description="Displayed equivalent Python code")
    r_code: str = Field(..., description="Displayed equivalent R code (generated via Jinja2)")
    plots: List[Dict[str, Any]] = Field(default_factory=list, description="Plotly figure JSON dictionaries")
    interpretation: str = Field(..., description="Plain-English interpretation of findings")
    warnings: List[str] = Field(default_factory=list, description="Important limitations or caveats")
    references: List[str] = Field(default_factory=list, description="Academic/statistical references")


class AnalysisRequest(BaseModel):
    """User request to execute a statistical method on a dataset."""
    dataset_id: str
    method_id: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)
    override_assumptions: bool = Field(False, description="If True, execute even if error-level assumptions fail")
    apply_auto_fix: bool = Field(True, description="If True, automatically apply auto_fix remedies (e.g. Welch correction)")


class AnalysisResponse(BaseModel):
    """API response wrapper for analysis execution."""
    status: Literal["success", "assumptions_failed", "error"]
    result: Optional[MethodResult] = None
    assumption_results: Optional[List[AssumptionResult]] = None
    message: Optional[str] = None


class IntentResult(BaseModel):
    """Structured output from the Natural Language Intent Parser."""
    status: Literal["clear", "ambiguous", "invalid"]
    method_id: Optional[str] = None
    method_name: Optional[str] = None
    variables: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)
    clarification_questions: List[str] = Field(default_factory=list)
    invalid_reason: Optional[str] = None
    ambiguous_variables: Dict[str, List[str]] = Field(default_factory=dict)
    user_intent_summary: Optional[str] = None
