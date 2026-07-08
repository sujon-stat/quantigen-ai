from typing import Any, Dict, List, Optional
from backend.app.services.chat.parser import NaturalLanguageIntentParser, IntentRecommendation
from backend.app.services.statistics.base import MethodResult
from backend.app.services.analysis.reporting import APAReportingService


class ChatConsultantService:
    """Manages conversational follow-ups, statistical education, and intent refinement for StatMind AI."""

    @classmethod
    def process_message(
        cls,
        message: str,
        history: List[Dict[str, str]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process incoming user chat message given recent conversation history and active analysis context.
        Returns a structured consultant response including recommended actions or pedagogical explanations.
        """
        msg_lower = message.lower()

        # 1. Check if asking about an active analysis or assumption failure
        active_analysis = context.get("current_analysis")
        if active_analysis and any(kw in msg_lower for kw in ["why", "what does", "explain", "meaning", "p-value", "assumption", "failed", "warning"]):
            explanation = cls._generate_educational_followup(message, active_analysis)
            return {
                "response_type": "educational_explanation",
                "message": explanation,
                "suggested_actions": ["Run post-hoc checks", "Download R script", "Try non-parametric alternative"] if "assumption" in msg_lower else ["Generate report"]
            }

        # 2. Check if user wants to change/tune parameters or methods
        if any(kw in msg_lower for kw in ["instead", "change to", "switch", "try", "use equal variance", "robust"]):
            return {
                "response_type": "parameter_adjustment",
                "message": "I understood your request to adjust the analysis options. You can re-run the analysis with updated parameter configurations or switch the target statistical procedure directly.",
                "suggested_actions": ["Update analysis configuration"]
            }

        # 3. Otherwise, treat as a new intent query to recommend a method
        columns_meta = context.get("columns_metadata", [])
        recommendation = NaturalLanguageIntentParser.parse_query(message, columns_meta)

        return {
            "response_type": "intent_recommendation",
            "recommendation": recommendation.model_dump(),
            "message": f"Based on your question, I recommend running a **{recommendation.method_name}**.\n\n**Why?** {recommendation.rationale}" + ("\n\n*Note: Please confirm the suggested variable bindings before execution.*" if recommendation.requires_confirmation else ""),
            "suggested_actions": [f"Execute {recommendation.method_name}"]
        }

    @classmethod
    def _generate_educational_followup(cls, question: str, analysis_context: Dict[str, Any]) -> str:
        """Generate tailored educational guidance based on active analysis results and assumptions."""
        q_lower = question.lower()
        method_name = analysis_context.get("method_name", "your statistical test")

        if "p-value" in q_lower or "p value" in q_lower or "significan" in q_lower:
            p_val = analysis_context.get("main_results", {}).get("p_value", 0.05)
            return (
                f"**Understanding the $p$-value ($p = {p_val:.4f}$) in {method_name}:**\n\n"
                f"The $p$-value represents the exact probability of observing data at least as extreme as yours assuming the null hypothesis (no effect or difference) is true.\n\n"
                f"- Because $p = {p_val:.4f}$ is **{'less than' if p_val < 0.05 else 'greater than'}** the standard $\\alpha = 0.05$ threshold, your finding is **{'statistically significant' if p_val < 0.05 else 'not statistically significant'}**.\n"
                f"- Remember that statistical significance does not always mean clinical or practical importance—always review the accompanying effect size (e.g., Cohen's $d$ or $R^2$) to gauge magnitude!"
            )

        if "assumption" in q_lower or "levene" in q_lower or "shapiro" in q_lower or "warning" in q_lower:
            assumptions = analysis_context.get("assumption_results", [])
            failed = [a for a in assumptions if not a.get("passed", True)]
            if failed:
                failed_str = "\n".join([f"- **{a.get('assumption_name')}**: {a.get('explanation')}" for a in failed])
                return (
                    f"**Why Assumption Checks Matter for {method_name}:**\n\n"
                    f"Every parametric statistical test relies on specific mathematical assumptions about your data distribution. When violated, standard error calculations and $p$-values can become distorted.\n\n"
                    f"**Detected Issues in Your Analysis:**\n{failed_str}\n\n"
                    f"**StatMind AI Protection:** Whenever possible, StatMind automatically applies robust corrections (such as Welch's degrees of freedom or HC3 robust standard errors) so your inferences remain reliable!"
                )
            else:
                return f"Good news! All diagnostic assumption checks for **{method_name}** passed successfully, confirming that your dataset meets the theoretical prerequisites for this test."

        if any(w in q_lower for w in ["apa", "report", "citation", "write up", "write-up", "manuscript"]):
            try:
                # Construct temporary MethodResult for APA reporting
                res = MethodResult(
                    method_id=analysis_context.get("method_id", "descriptive"),
                    method_name=method_name,
                    method_family=analysis_context.get("method_family", "General"),
                    description=analysis_context.get("description", ""),
                    variables_used=analysis_context.get("variables_used", {}),
                    sample_size=analysis_context.get("sample_size", 0),
                    python_code=analysis_context.get("python_code", ""),
                    r_code=analysis_context.get("r_code", ""),
                    interpretation=analysis_context.get("interpretation", ""),
                    main_results=analysis_context.get("main_results", {}),
                    effect_sizes=analysis_context.get("effect_sizes", {})
                )
                citation = APAReportingService.generate_apa_citation(res)
                return (
                    f"**APA 7th Edition Publication Citation for {method_name}:**\n\n"
                    f"> {citation}\n\n"
                    f"You can directly copy and paste this text into your academic manuscript or thesis! For high-resolution static publication figures (`.png` / 300 DPI), use our `POST /api/v1/export/report` endpoint with `format='html_manuscript'`."
                )
            except Exception:
                pass

        if any(w in q_lower for w in ["effect size", "cohen", "r2", "eta", "magnitude", "practical"]):
            effect = analysis_context.get("effect_sizes", {})
            effect_summary = ", ".join(f"**{k}**: {v}" for k, v in effect.items() if isinstance(v, (int, float, str)))
            return (
                f"**Practical Significance & Effect Size in {method_name}:**\n\n"
                f"While $p$-values tell you whether an effect exists beyond random chance, the **effect size** measures how strong or meaningful that effect actually is in the real world.\n\n"
                f"**Current Effect Size Metrics:**\n{effect_summary or 'See exact metrics in your analysis output.'}\n\n"
                f"- **Small effect**: Noticeable only with careful measurement across large samples.\n"
                f"- **Medium effect**: Large enough to be visible to the naked eye or clinically meaningful.\n"
                f"- **Large effect**: Substantial and unmistakable impact on the outcome variable."
            )

        return (
            f"**Consultant Insights on {method_name}:**\n\n"
            f"StatMind AI guarantees full transparency and assumption-first analysis. Your current analysis evaluates relationships across $n={analysis_context.get('sample_size', 'unknown')}$ observations.\n\n"
            f"Feel free to ask me for an **APA 7th edition citation**, explanation of **effect sizes**, specific statistical definitions, or request an exportable R script of your results!"
        )
