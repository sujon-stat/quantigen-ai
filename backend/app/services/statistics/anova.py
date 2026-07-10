import numpy as np
import pandas as pd
from scipy import stats
from typing import Any, Dict, List, Optional
from backend.app.models.analysis import MethodResult
from backend.app.core.exceptions import StatisticalViolationException
from backend.app.services.statistics.base import BaseStatisticalMethod
from backend.app.services.r_integration.code_gen import CodeGenerator
from backend.app.services.visualization import plotter


class OneWayAnovaMethod(BaseStatisticalMethod):
    method_id = "anova_oneway"
    method_name = "One-Way ANOVA"
    method_family = "ANOVA & Multi-Group Comparisons"
    description = "Compares the means of a continuous dependent variable across three or more independent groups."
    required_variables = {
        "dependent": ["continuous"],
        "grouping": ["categorical"]
    }
    optional_variables = {}

    def run(self, data: pd.DataFrame, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> MethodResult:
        options = options or {}
        errors = self.validate_variables(data, variables)
        if errors:
            raise StatisticalViolationException(message=f"Variable validation failed: {', '.join(errors)}", violation_type="variable_validation")

        dep_var = variables["dependent"]
        group_var = variables["grouping"]

        df_clean = data[[dep_var, group_var]].dropna()
        # Convert grouping variable cleanly to string/category so numbers or strings work uniformly
        df_clean[group_var] = df_clean[group_var].astype(str)
        # Filter out groups with fewer than 2 observations to ensure valid variances and degrees of freedom
        group_counts = df_clean[group_var].value_counts()
        valid_groups = group_counts[group_counts >= 2].index.tolist()
        
        if len(valid_groups) < 2:
            # If after filtering n>=2 there aren't at least 2 groups, take top 2 groups with at least n>=1
            valid_groups = group_counts.index[:max(2, min(10, len(group_counts)))].tolist()
            if len(valid_groups) < 2:
                raise StatisticalViolationException(
                    message=f"Grouping variable '{group_var}' must have at least 2 distinct categories.",
                    violation_type="grouping_levels_violation",
                    remedy="Please select a categorical or grouping column with at least 2 distinct levels."
                )

        # If more than 30 distinct levels (e.g. CGPA or high-cardinality), select the top 30 most frequent groups for One-Way ANOVA
        if len(valid_groups) > 30:
            valid_groups = valid_groups[:30]

        df_clean = df_clean[df_clean[group_var].isin(valid_groups)]
        groups = valid_groups
        group_series = [pd.to_numeric(df_clean[df_clean[group_var] == g][dep_var], errors='coerce').dropna() for g in groups]
        # Remove any empty series
        valid_pairs = [(g, s) for g, s in zip(groups, group_series) if len(s) >= 1]
        groups = [p[0] for p in valid_pairs]
        group_series = [p[1] for p in valid_pairs]
        
        n_total = sum(len(s) for s in group_series)
        k = len(groups)

        # 1. Check Assumptions
        assumptions = self.check_assumptions(data, variables)

        # Check Levene's test outcome for Welch's ANOVA auto-fix
        levene_passed = True
        for a in assumptions:
            if a.assumption_name == "homogeneity_variance":
                levene_passed = a.passed

        if "equal_var" in options:
            equal_var = bool(options["equal_var"])
        else:
            equal_var = levene_passed

        # 2. Main Analysis: Standard OLS ANOVA or Welch's ANOVA
        if equal_var and k >= 2 and all(len(s) >= 1 for s in group_series):
            try:
                f_stat, p_val = stats.f_oneway(*group_series)
                if np.isnan(f_stat) or np.isnan(p_val):
                    raise ValueError("NaN F-stat")
                dof_between = float(k - 1)
                dof_within = float(max(1, n_total - k))
                test_type = "Standard One-Way ANOVA (F-Test)"
            except Exception:
                equal_var = False

        if not equal_var:
            # Resilient Welch's ANOVA calculation using scipy.stats across groups
            weights = []
            for g in group_series:
                var_g = float(g.var(ddof=1)) if len(g) >= 2 else 1e-6
                w = len(g) / var_g if var_g > 1e-12 else float(len(g)) * 1e6
                weights.append(w)
            
            w_sum = sum(weights) if sum(weights) > 0 else 1e-9
            y_bar_w = sum(w * float(g.mean()) for w, g in zip(weights, group_series)) / w_sum
            
            num = sum(w * ((float(g.mean()) - y_bar_w)**2) for w, g in zip(weights, group_series)) / max(1, k - 1)
            lam = sum((1.0 / max(1, len(g) - 1)) * (1.0 - w / w_sum)**2 for w, g in zip(weights, group_series))
            denom = 1.0 + (2.0 * (k - 2) / max(1, k**2 - 1)) * lam
            
            f_stat = float(num / denom) if denom > 0 else 0.0
            dof_between = float(max(1, k - 1))
            dof_within = float((k**2 - 1) / (3.0 * lam)) if lam > 1e-12 else float(max(1, n_total - k))
            p_val = float(stats.f.sf(f_stat, dof_between, dof_within))
            test_type = "Welch's One-Way ANOVA (Unequal Variances Adjusted)"

        # Group summaries
        group_summaries = []
        for g_name, g_s in zip(groups, group_series):
            group_summaries.append({
                "name": str(g_name),
                "n": len(g_s),
                "mean": float(g_s.mean()),
                "std": float(g_s.std()),
                "se": float(g_s.std() / np.sqrt(len(g_s)))
            })

        main_results = {
            "test_type": test_type,
            "f_statistic": float(f_stat),
            "degrees_of_freedom_between": float(dof_between),
            "degrees_of_freedom_within": float(dof_within),
            "p_value": float(p_val),
            "k_groups": k,
            "group_summaries": group_summaries
        }

        # 3. Effect Size: Eta-Squared (eta^2) and Omega-Squared (omega^2)
        grand_mean = df_clean[dep_var].mean()
        ss_total = float(sum((df_clean[dep_var] - grand_mean)**2))
        ss_between = float(sum(len(g) * ((g.mean() - grand_mean)**2) for g in group_series))
        ss_within = ss_total - ss_between
        ms_within = ss_within / (n_total - k) if (n_total - k) > 0 else 0.0

        eta_squared = ss_between / ss_total if ss_total > 0 else 0.0
        omega_squared = (ss_between - (k - 1) * ms_within) / (ss_total + ms_within) if (ss_total + ms_within) > 0 else 0.0
        omega_squared = max(0.0, float(omega_squared))

        effect_sizes = {
            "eta_squared": float(eta_squared),
            "omega_squared": float(omega_squared),
            "interpretation": "Negligible" if eta_squared < 0.01 else ("Small" if eta_squared < 0.06 else ("Medium" if eta_squared < 0.14 else "Large"))
        }

        # 4. Post-Hoc Pairwise Comparisons (Tukey's HSD)
        post_hoc_results = None
        if p_val < 0.05 and k >= 3:
            try:
                res = stats.tukey_hsd(*group_series)
                comparisons = []
                for i in range(k):
                    for j in range(i + 1, k):
                        diff = float(group_series[i].mean() - group_series[j].mean())
                        p_adj = float(res.pvalue[i, j])
                        ci_low = float(res.confidence_interval(confidence_level=0.95).low[i, j])
                        ci_high = float(res.confidence_interval(confidence_level=0.95).high[i, j])
                        comparisons.append({
                            "group1": str(groups[i]),
                            "group2": str(groups[j]),
                            "mean_difference": diff,
                            "p_value_adjusted": p_adj,
                            "ci_95_lower": ci_low,
                            "ci_95_upper": ci_high,
                            "significant": bool(p_adj < 0.05)
                        })
                post_hoc_results = {
                    "test_name": "Tukey's Honestly Significant Difference (HSD)",
                    "comparisons": comparisons
                }
            except Exception as e:
                post_hoc_results = {"error": f"Failed to compute Tukey HSD: {str(e)}"}

        # 5. Code Generation
        r_context = {
            "dep_var": dep_var,
            "group_var": group_var,
            "conf_level": options.get("conf_level", 0.95)
        }
        r_code = self.generate_r_code(variables, r_context)
        py_code = self._generate_python_code(dep_var, group_var, equal_var)

        # 6. Plots
        plots = self.generate_plots(df_clean, variables, main_results)

        # 7. Interpretation
        interpretation = self.interpret({"main": main_results, "effect": effect_sizes, "post_hoc": post_hoc_results}, variables)

        warnings = []
        if not equal_var:
            warnings.append("Levene's test indicated unequal variances across groups. Welch's ANOVA correction was automatically applied to maintain accurate Type I error rates.")

        return MethodResult(
            method_id=self.method_id,
            method_name=self.method_name,
            method_family=self.method_family,
            description=self.description,
            variables_used=variables,
            sample_size=n_total,
            assumption_results=assumptions,
            main_results=main_results,
            effect_sizes=effect_sizes,
            post_hoc_results=post_hoc_results,
            python_code=py_code,
            r_code=r_code,
            plots=plots,
            interpretation=interpretation,
            warnings=warnings,
            references=[
                "Welch, B. L. (1951). On the comparison of several mean values: An alternative approach. Biometrika, 38(3/4), 330-336.",
                "Tukey, J. W. (1949). Comparing individual means in the analysis of variance. Biometrics, 5(2), 99-114.",
                "Cohen, J. (1988). Statistical power analysis for the behavioral sciences (2nd ed.)."
            ]
        )

    def generate_r_code(self, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> str:
        options = options or {}
        return CodeGenerator.render_r_template("anova.R.j2", options)

    def _generate_python_code(self, dep_var: str, group_var: str, equal_var: bool) -> str:
        code = f"""import pandas as pd
import scipy.stats as stats
import numpy as np

# Prepare clean data
clean_df = data[['{dep_var}', '{group_var}']].dropna()
groups = clean_df['{group_var}'].unique()
group_series = [clean_df[clean_df['{group_var}'] == g]['{dep_var}'] for g in groups]

print(f"One-Way ANOVA comparing {{len(groups)}} groups across '{dep_var}' (n={{len(clean_df)}})")

# Run Standard One-Way ANOVA F-test
f_stat, p_value = stats.f_oneway(*group_series)
print(f"F-Statistic: {{f_stat:.4f}}, p-value: {{p_value:.4f}}")

# Calculate Eta-Squared effect size
grand_mean = clean_df['{dep_var}'].mean()
ss_total = sum((clean_df['{dep_var}'] - grand_mean)**2)
ss_between = sum(len(g) * ((g.mean() - grand_mean)**2) for g in group_series)
eta_squared = ss_between / ss_total
print(f"Eta-Squared: {{eta_squared:.4f}}")

# Run Tukey's HSD Post-Hoc Test if p < 0.05
if p_value < 0.05 and len(groups) >= 3:
    tukey_res = stats.tukey_hsd(*group_series)
    print("\\nTukey HSD Pairwise Comparisons:")
    print(tukey_res)
"""
        return CodeGenerator.format_python_code(self.method_name, code)

    def generate_plots(self, data: pd.DataFrame, variables: Dict[str, Any], results: Dict[str, Any]) -> List[Dict[str, Any]]:
        dep_var = variables["dependent"]
        group_var = variables["grouping"]

        p1 = plotter.plot_boxplot_jitter(
            data=data,
            dep_var=dep_var,
            group_var=group_var,
            title=f"One-Way ANOVA: Distribution of {dep_var} by {group_var}"
        )

        groups = data[group_var].unique()
        series_dict = {str(grp): data[data[group_var] == grp][dep_var] for grp in groups}
        p2 = plotter.plot_qq_normality(
            series_dict=series_dict,
            title=f"Normality Q-Q Plot of {dep_var} within each Group",
            subtitle="Points adhering closely to the dashed diagonal line indicate normality within group"
        )

        p3 = plotter.plot_means_ci(
            data=data,
            dep_var=dep_var,
            group_var=group_var,
            title=f"Group Means and 95% Confidence Intervals: {dep_var} by {group_var}"
        )

        return [p1, p2, p3]

    def interpret(self, results: Dict[str, Any], variables: Dict[str, Any]) -> str:
        main = results["main"]
        effect = results["effect"]
        post_hoc = results.get("post_hoc")
        dep = variables["dependent"]
        grp = variables["grouping"]

        p_val = main["p_value"]
        sig_str = "statistically significant" if p_val < 0.05 else "not statistically significant"
        p_display = f"p < 0.001" if p_val < 0.001 else f"p = {p_val:.3f}"

        lines = [
            f"A **{main['test_type']}** was conducted to compare **{dep}** across **{main['k_groups']}** groups of **{grp}** ($n={results.get('sample_size', 'N')}$).",
            f"\n**Main Findings:**",
            f"- There was a {sig_str} overall difference in mean **{dep}** between the groups ($F({main['degrees_of_freedom_between']:.2f}, {main['degrees_of_freedom_within']:.2f}) = {main['f_statistic']:.2f}, {p_display}$).",
            f"\n**Effect Size:**",
            f"- The proportion of variance explained by group membership ($\\eta^2$) is **{effect['eta_squared']:.3f}** (with $\\omega^2 = {effect['omega_squared']:.3f}$), representing a **{effect['interpretation'].lower()}** practical effect."
        ]

        if post_hoc and "comparisons" in post_hoc:
            sig_pairs = [c for c in post_hoc["comparisons"] if c["significant"]]
            lines.append("\n**Post-Hoc Pairwise Comparisons (Tukey's HSD):**")
            if sig_pairs:
                for sp in sig_pairs:
                    lines.append(f"- **{sp['group1']} vs {sp['group2']}**: Mean difference = **{sp['mean_difference']:.2f}** ($p_{{adj}} = {sp['p_value_adjusted']:.3f}$, 95% CI [{sp['ci_95_lower']:.2f}, {sp['ci_95_upper']:.2f}]).")
            else:
                lines.append("- None of the specific pairwise comparisons achieved statistical significance after multiple comparison adjustment.")

        return "\n".join(lines)
