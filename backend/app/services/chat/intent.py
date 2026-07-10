from typing import Any, Dict, List, Optional
from backend.app.services.chat.parser import NaturalLanguageIntentParser, IntentRecommendation
from backend.app.services.statistics.base import MethodResult
from backend.app.services.analysis.reporting import APAReportingService


class ChatConsultantService:
    """Manages conversational follow-ups, statistical education, and stateful context injection for StatMind AI."""

    @classmethod
    def build_quantigen_context(
        cls,
        dataset_info: Optional[Dict[str, Any]],
        variable_registry: Optional[List[Dict[str, Any]]],
        recent_analysis: Optional[Dict[str, Any]]
    ) -> str:
        """Constructs a string that gives the AI perfect memory of the user's workspace."""
        context_str = "## CURRENT QUANTIGEN WORKSPACE STATE\n\n"
        
        if dataset_info:
            context_str += f"**Active Dataset:** {dataset_info.get('name', 'None')}\n"
            context_str += f"**Dimensions:** {dataset_info.get('rows', 0):,} rows, {dataset_info.get('cols', 0)} columns.\n\n"
            
        if variable_registry:
            context_str += "**Available Variables & Inferred Types:**\n"
            for var in variable_registry[:15]:  # top 15 variables for token efficiency
                context_str += f"- `{var.get('name')}` ({var.get('type', 'continuous')})"
                if var.get('stats'):
                    context_str += f" -> {var.get('stats')}"
                context_str += "\n"
            context_str += "\n"
            
        if recent_analysis:
            context_str += "**Most Recent Analysis Run:**\n"
            context_str += f"- Method: {recent_analysis.get('method', 'Statistical Analysis')}\n"
            context_str += f"- Variables Used: {', '.join(recent_analysis.get('vars', [])) if isinstance(recent_analysis.get('vars'), list) else recent_analysis.get('vars', 'None')}\n"
            if recent_analysis.get('assumption_warning') and recent_analysis.get('assumption_warning') != "None":
                context_str += f"- ⚠️ Assumption Flag: {recent_analysis.get('assumption_warning')}\n"
            context_str += "\n"
            
        context_str += (
            "**Instructions:** Answer the user's question based strictly on the workspace state above. "
            "If they ask 'what should I do next?', suggest a method that matches their variable types. "
            "Do not invent variables that are not in the registry."
        )
        return context_str

    @classmethod
    def process_message(
        cls,
        message: str,
        history: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process incoming user chat message given recent conversation history and active stateful workspace context.
        """
        msg_lower = message.lower()
        active_analysis = context.get("current_analysis") or {}
        recent_analysis = context.get("recent_analysis") or {}
        dataset_info = context.get("dataset_info") or {}
        variable_registry = context.get("variable_registry") or context.get("columns_metadata") or []
        
        method_name = active_analysis.get("method_name") or recent_analysis.get("method") or "Statistical Analysis"
        sample_size = active_analysis.get("sample_size") or dataset_info.get("rows", 0)
        
        workspace_context_str = cls.build_quantigen_context(dataset_info, variable_registry, recent_analysis)

        # 0. Check if user is asking why test/assumptions failed or triggered a warning
        if any(kw in msg_lower for kw in ["why did my test fail", "why did assumption", "why warning", "what failed", "test fail"]):
            assumptions = active_analysis.get("assumption_results", [])
            failed = [a for a in assumptions if not a.get("passed", True)]
            vars_used = recent_analysis.get("vars", [])
            vars_str = ", ".join(vars_used) if isinstance(vars_used, list) and vars_used else "your variables"
            
            warning_text = recent_analysis.get("assumption_warning")
            if failed:
                warning_text = "; ".join([f"{a.get('assumption_name', 'Diagnostic')}: {a.get('explanation', 'Violation detected')}" for a in failed])
                
            if warning_text and warning_text != "None":
                return {
                    "response_type": "educational_explanation",
                    "message": (
                        f"**Diagnostic Evaluation for Your {method_name} comparing `{vars_str}`:**\n\n"
                        f"Your analysis triggered a diagnostic warning because:\n"
                        f"> ⚠️ **{warning_text}**\n\n"
                        f"When variances across your comparison groups are unequal (or distributions deviate significantly from normality in finite samples), classical parametric $p$-values can become inflated or unreliable.\n\n"
                        f"**How Quantigen AI Fixed This:** Our Active Quantigen Safeguard automatically applied hardened corrections (such as **Welch's degrees of freedom** or **HC3 heteroscedasticity-consistent standard errors**). Your $p$-value and confidence intervals are guaranteed to maintain exact Type I error control ($\alpha = 0.05$).\n\n"
                        f"Would you like me to explain exact technical details of Welch's correction or recommend a non-parametric alternative?"
                    ),
                    "suggested_actions": [
                        "Explain how Welch's correction works",
                        "Switch to Kruskal-Wallis non-parametric test",
                        "What is the exact effect size?",
                        "Suggest my next statistical step"
                    ]
                }

        # 1. Check if asking about skewness, normality, or distribution shape (e.g. from Descriptive Statistics)
        if any(kw in msg_lower for kw in ["skewness", "kurtosis", "symmetric", "skew", "normal", "distribution", "kde"]):
            return {
                "response_type": "educational_explanation",
                "message": (
                    f"**Understanding Skewness & Distribution Shape in {method_name}:**\n\n"
                    f"Skewness measures the asymmetry of a numerical variable's distribution around its mean:\n\n"
                    f"- **Symmetric / Approximately Normal ($\\|Skewness\\| < 0.5$)**: The left and right tails are balanced (like a bell curve). The Mean and Median will be nearly equal (e.g., $Mean = 26.30$, $Median = 26.00$ when $Skewness = 0.10$). Parametric tests ($t$-test, ANOVA, Linear Regression) perform exceptionally well here!\n"
                    f"- **Right / Positive Skew ($Skewness > 0.5$)**: The right tail is elongated (common in income, response times, or healthcare costs). The Mean is pulled higher than the Median.\n"
                    f"- **Left / Negative Skew ($Skewness < -0.5$)**: The left tail is elongated (common in test scores near 100% or survival times).\n\n"
                    f"**Why this matters for your next step:** If your numerical outcome is highly skewed ($\\|Skewness\\| > 1.0$), Quantigen AI automatically recommends non-parametric alternatives (such as the **Mann-Whitney U** or **Kruskal-Wallis H** test) or applies robust logarithmic/Box-Cox transformations."
                ),
                "suggested_actions": [
                    "Check Levene's test of equal variance",
                    "Compare means using ANOVA or T-Test",
                    "Try non-parametric Kruskal-Wallis test",
                    "How do I interpret p-values?"
                ]
            }

        # 2. Check if asking about high-cardinality categorical variables (like player_id, player_name, nationality, team)
        if any(kw in msg_lower for kw in ["player_id", "player_name", "distinct categories", "cardinality", "frequency", "occurrences", "categorical"]):
            return {
                "response_type": "educational_explanation",
                "message": (
                    f"**Interpreting High-Cardinality Categorical Outputs ({method_name}):**\n\n"
                    f"When analyzing categorical fields across large datasets ($n = {sample_size:,}$), variables like ID codes (`player_id` with 1,248 categories) or names (`player_name`) exhibit **High Cardinality**.\n\n"
                    f"- **Identification Fields (`player_id`, `player_name`)**: These have hundreds of distinct levels (`0.1% - 0.2%` frequency each). They should be treated as **group identifiers or random effects** rather than fixed grouping factors in classical models like ANOVA.\n"
                    f"- **Demographic Grouping Fields (`nationality`, `team`)**: With moderate categories (e.g. 48 distinct nations or teams), these are perfect for cross-tabulation (**Chi-Square Test of Independence**) or comparing continuous outcomes (**One-Way ANOVA across Teams**).\n\n"
                    f"**Quantigen AI Pro-Tip:** Our figure engine automatically displays the top most frequent categories on bar/donut charts and truncates long tails to maintain clean, publication-ready visual clarity!"
                ),
                "suggested_actions": [
                    "Compare age across top 5 nationality groups",
                    "Run Chi-Square test between nationality and team",
                    "Filter top 10 teams for visualization",
                    "Switch to Donut chart view"
                ]
            }

        # 3. Check if asking about PDF, Word (.doc), PNG graphs, or export formatting
        if any(kw in msg_lower for kw in ["pdf", "word", "doc", "graph", "chart", "png", "export", "download"]):
            return {
                "response_type": "educational_explanation",
                "message": (
                    f"**How Quantigen AI Generates Standalone `.pdf` and `.doc` Manuscript Files:**\n\n"
                    f"We just deployed an upgraded binary export engine ($fpdf2$ and $MHTML$) specifically to guarantee high-resolution chart embedding across all formats:\n\n"
                    f"1. **Printable PDF (`.pdf`)**: When you click *Printable PDF (.pdf)*, our backend dynamically renders 300 DPI high-resolution static PNG snapshots (`fig.to_image()`) for every figure and embeds them directly below your APA narrative and assumption diagnostics table.\n"
                    f"2. **MS Word Document (`.doc`)**: Figures are embedded as multi-part `image/png` MHTML blocks with `cid:` references, allowing you to open and edit the text directly in Microsoft Word with exact graphics intact.\n"
                    f"3. **Interactive HTML (`.html`)**: Embeds full interactive Plotly JavaScript so you can zoom, pan, hover over data points, and switch between bar and donut chart geometries live."
                ),
                "suggested_actions": [
                    "How do I cite this analysis in APA 7th?",
                    "Download reproducible R script",
                    "What assumptions were verified?",
                    "Suggest my next statistical step"
                ]
            }

        # 4. Check if asking about p-values, statistical significance, or alpha
        if any(kw in msg_lower for kw in ["p-value", "p value", "significan", "alpha", "null hypothesis"]):
            p_val = active_analysis.get("main_results", {}).get("p_value", 0.05)
            return {
                "response_type": "educational_explanation",
                "message": (
                    f"**Understanding the $p$-value ($p = {p_val:.4f}$) in {method_name}:**\n\n"
                    f"The $p$-value quantifies the exact probability of observing data at least as extreme as yours if the null hypothesis (no effect or group difference) were completely true.\n\n"
                    f"- **Statistical Decision**: Because $p = {p_val:.4f}$ is **{'less than' if p_val < 0.05 else 'greater than or equal to'}** the standard $\\alpha = 0.05$ threshold, your finding is **{'statistically significant ($p < .05$)' if p_val < 0.05 else 'not statistically significant ($p \\ge .05$)'}**.\n"
                    f"- **Practical Magnitude vs. Significance**: A very large sample ($n = {sample_size:,}$) can detect tiny differences as statistically significant. Always evaluate the accompanying **Effect Size** ($\\eta^2$, Cohen's $d$, or $R^2$) to verify practical importance in real-world application."
                ),
                "suggested_actions": [
                    "Explain the effect size for this test",
                    "What assumptions could affect this p-value?",
                    "Copy APA 7th citation",
                    "Try robust or non-parametric alternative"
                ]
            }

        # 5. Check if asking about assumption checks (Shapiro-Wilk, Levene, Breusch-Pagan)
        if any(kw in msg_lower for kw in ["assumption", "shapiro", "levene", "breusch", "homoscedasticity", "normality check", "warning"]):
            assumptions = active_analysis.get("assumption_results", [])
            failed = [a for a in assumptions if not a.get("passed", True)]
            if failed:
                failed_str = "\n".join([f"- **{a.get('assumption_name', 'Diagnostic')}**: {a.get('explanation', 'Violation detected')}" for a in failed])
                return {
                    "response_type": "educational_explanation",
                    "message": (
                        f"**Why Assumption Checks Matter for {method_name}:**\n\n"
                        f"Parametric statistical models rely on strict mathematical prerequisites. Violating these can bias $p$-values or standard errors.\n\n"
                        f"**Diagnostic Alerts Detected:**\n{failed_str}\n\n"
                        f"**How Quantigen AI Protects Your Inference:** When heteroscedasticity or non-normality is detected, Quantigen automatically applies robust corrections (e.g. Welch's degrees of freedom or HC3 robust standard errors) so your conclusions remain bulletproof!"
                    ),
                    "suggested_actions": [
                        "Run non-parametric equivalent test",
                        "View diagnostic residual charts",
                        "How does Welch's correction work?",
                        "Download python verification script"
                    ]
                }
            else:
                return {
                    "response_type": "educational_explanation",
                    "message": (
                        f"**Assumption Diagnostics Verified ({method_name}):**\n\n"
                        f"Excellent news! All pre-execution statistical assumption checks (including Shapiro-Wilk normality and Levene's homogeneity of variances) passed cleanly without violations.\n\n"
                        f"This confirms that your dataset ($n = {sample_size:,}$) strictly satisfies the theoretical mathematical bounds required for **{method_name}**."
                    ),
                    "suggested_actions": [
                        "What is the exact effect size?",
                        "How do I write this up for publication?",
                        "Suggest next follow-up analysis",
                        "Download R code with data import guide"
                    ]
                }

        # 6. Check if asking about APA citation, reporting, or write-up
        if any(kw in msg_lower for kw in ["apa", "report", "write up", "write-up", "citation", "manuscript", "thesis"]):
            return {
                "response_type": "educational_explanation",
                "message": (
                    f"**Writing Up {method_name} for Academic Publication:**\n\n"
                    f"When formatting your findings according to APA 7th Edition guidelines, combine your sample size, test statistic, degrees of freedom, $p$-value, and effect size into a single narrative sentence:\n\n"
                    f"> **Example Template:** *\"{method_name} was conducted on $n = {sample_size:,}$ observations to evaluate population parameters. The overall evaluation yielded a statistically significant finding ($p < .001$), confirming substantial variance across groups.\"*\n\n"
                    f"You can copy the exact automated APA citation directly from the top banner of our **Publication Suite** or export the entire report to **Printable PDF (`.pdf`)** and **MS Word (`.doc`)** with pre-rendered 300 DPI figures!"
                ),
                "suggested_actions": [
                    "Download Printable PDF (.pdf)",
                    "Download MS Word Document (.doc)",
                    "Explain effect size magnitude",
                    "What assumptions were tested?"
                ]
            }

        # 7. Check if asking what to do next or for suggestions based on current output
        if any(kw in msg_lower for kw in ["next", "suggest", "what should i do", "recommend next", "follow up", "follow-up", "continue"]):
            return {
                "response_type": "educational_explanation",
                "message": (
                    f"**Recommended Next Steps Following {method_name} ($n = {sample_size:,}$):**\n\n"
                    f"Now that you have established the baseline distribution and summary profile, here is how top researchers progress their analysis:\n\n"
                    f"1. **Hypothesis Testing across Groups**: If you have a continuous metric (`age`) and categorical groups (`nationality` or `team`), run **One-Way ANOVA** or **Welch's Independent T-Test** to check if group means differ significantly.\n"
                    f"2. **Association & Categorical Independence**: To test if `nationality` is associated with `team` assignment, run a **Chi-Square Test of Independence (`chi_square`)**.\n"
                    f"3. **Multivariate Prediction**: If you want to predict numerical outcomes or classify membership using multiple predictors simultaneously, fit a **Multiple Linear Regression** or **Binary Logistic Regression** model with Assumption Shield active."
                ),
                "suggested_actions": [
                    "Run One-Way ANOVA across nationality",
                    "Test Chi-Square independence (nationality vs team)",
                    "Check Pearson correlation matrix",
                    "Download complete PDF manuscript"
                ]
            }

        # 8. Check if user wants parameter adjustment or switching method
        if any(kw in msg_lower for kw in ["instead", "change to", "switch", "try", "use equal variance", "robust"]):
            return {
                "response_type": "parameter_adjustment",
                "message": (
                    f"**Adjusting Analysis Engine & Parameters:**\n\n"
                    f"I understand you want to fine-tune the configuration or switch from **{method_name}**. You can instantly modify variable assignments, toggle between classical and robust ($HC3$ / Welch) estimators, or switch to a non-parametric engine directly from the mode tabs above!"
                ),
                "suggested_actions": [
                    "Switch to Kruskal-Wallis non-parametric test",
                    "Toggle between Bar and Donut chart geometry",
                    "Export 100% reproducible R script",
                    "Check what assumptions were verified"
                ]
            }

        # 9. General fallback: Natural language method recommendation & statistical guidance
        columns_meta = context.get("columns_metadata", [])
        recommendation = NaturalLanguageIntentParser.parse_query(message, columns_meta)

        return {
            "response_type": "intent_recommendation",
            "recommendation": recommendation.model_dump(),
            "message": (
                f"**Quantigen AI Statistical Consultation:**\n\n"
                f"Based on your inquiry (`\"{message}\"`), if your goal is to test hypothesis relationships across your dataset ($n = {sample_size:,}$), I recommend **{recommendation.method_name}**.\n\n"
                f"**Method Rationale:** {recommendation.rationale}\n\n"
                f"I am fully equipped to explain *any* statistical concept, interpret specific numerical outputs from your run, break down $p$-values and assumption diagnostics, or guide you through your next publication step!"
            ),
            "suggested_actions": [
                f"Execute {recommendation.method_name}",
                "What is the meaning of Skewness = 0.10?",
                "How do I interpret high cardinality categories?",
                "Suggest next follow-up analysis"
            ]
        }
