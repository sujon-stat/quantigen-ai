from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Dict, Literal, Optional


class Severity(str, Enum):
    """Severity levels for assumption violations."""
    ERROR = "error"           # Cannot proceed. Test is invalid.
    WARNING = "warning"       # Can proceed but results may be unreliable.
    AUTO_FIX = "auto_fix"     # System can automatically apply a remedy.


class AssumptionRule(BaseModel):
    """Definition of a single assumption to check."""
    name: str = Field(..., description="Short identifier e.g., 'normality'")
    description: str = Field(..., description="Human-readable description e.g., 'Normality of Residuals'")
    test_name: str = Field(..., description="Statistical test to run e.g., 'Shapiro-Wilk'")
    threshold: Optional[float] = Field(None, description="P-value or statistic threshold")
    severity: Severity = Field(..., description="What to do if violated")
    consequence: str = Field(..., description="What violation means e.g., 'Type I error rate inflated'")
    remedy: str = Field(..., description="How to fix or adapt to violation")
    alternative_method: Optional[str] = Field(None, description="Suggested alternative if can't fix e.g., 'Mann-Whitney U'")
    auto_fix_action: Optional[str] = Field(None, description="Code/key for automatic fix e.g., 'welch_t'")


class AssumptionResult(BaseModel):
    """Result of a single assumption check run against user data."""
    assumption_name: str
    passed: bool
    test_used: str
    test_statistic: Optional[float] = None
    p_value: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    explanation: str
    remedy: str
    auto_fix_available: bool = False
    auto_fix_description: Optional[str] = None
    severity: Severity = Severity.WARNING
