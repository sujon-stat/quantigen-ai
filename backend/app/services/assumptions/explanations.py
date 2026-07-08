from typing import Any, Dict, Optional
from backend.app.models.assumptions import AssumptionRule, Severity


def generate_explanation(
    rule: AssumptionRule,
    passed: bool,
    test_statistic: Optional[float] = None,
    p_value: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None,
    adjusted_severity: Optional[Severity] = None
) -> str:
    """Generate professional, educational human explanation of an assumption check outcome."""
    details = details or {}
    severity = adjusted_severity or rule.severity
    
    if passed:
        stat_str = f" (test statistic = {test_statistic:.2f}, p = {p_value:.3f})" if test_statistic is not None and p_value is not None else ""
        return f"✅ **Met**: The assumption of **{rule.description}** is satisfied{stat_str}. You can proceed confident in the standard statistical procedure."
    
    # If violated
    stat_info = []
    if test_statistic is not None:
        stat_info.append(f"test statistic = {test_statistic:.2f}")
    if p_value is not None:
        stat_info.append(f"p = {p_value:.3f}")
    stat_str = f" ({', '.join(stat_info)})" if stat_info else ""
    
    icon = "⚠️" if severity == Severity.WARNING else ("🔧" if severity == Severity.AUTO_FIX else "❌")
    status_label = "Warning" if severity == Severity.WARNING else ("Auto-Fix Available" if severity == Severity.AUTO_FIX else "Not Met")
    
    paragraphs = [
        f"{icon} **{rule.description} Check: {status_label}**{stat_str}",
        f"\n**What this means for your analysis:**\n{rule.consequence}"
    ]
    
    # Add CLT or sample size notes if in details
    if details.get("clt_applied"):
        sample_size = details.get("sample_size", "large")
        paragraphs.append(f"\n*Note*: With your sample size ($n = {sample_size}$), the test is moderately robust to this violation due to the Central Limit Theorem.")
    
    paragraphs.append(f"\n**Recommended Action:**\n{rule.remedy}")
    
    if rule.alternative_method:
        paragraphs.append(f"\n*Alternative method available*: `{rule.alternative_method}`")
        
    return "\n".join(paragraphs)
