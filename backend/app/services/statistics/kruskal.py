import numpy as np
import pandas as pd
from scipy import stats
from typing import Any, Dict, List, Optional
from backend.app.models.analysis import MethodResult
from backend.app.services.statistics.base import BaseStatisticalMethod
from backend.app.services.r_integration.code_gen import CodeGenerator
from backend.app.services.visualization import plotter


class KruskalWallisMethod(BaseStatisticalMethod):
    method_id = "kruskal_wallis"
    method_name = "Kruskal-Wallis H Test"
    method_family = "Non-Parametric Multi-Group Comparisons"
    description = "Compares median and rank distributions of an ordinal or non-normal continuous variable across three or more independent groups."
    required_variables = {
        "dependent": ["continuous", "ordinal"],
        "grouping": ["categorical"]
    }
    optional_variables = {}

    def run(self, data: pd.DataFrame, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> MethodResult:
        options = options or {}
        errors = self.validate_variables(data, variables)
        if errors:
            raise ValueError(f"Variable validation failed: {', '.join(errors)}")

        dep_var = variables["dependent"]
        group_var = variables["grouping"]

        df_clean = data[[dep_var, group_var]].dropna()
        groups = df_clean[group_var].unique()
        if len(groups) < 2:
            raise ValueError(f"Grouping variable '{group_var}' must have at least 2 distinct levels, found {len(groups)}.")

        group_series = [df_clean[df_clean[group_var] == g][dep_var] for g in groups]
        n_total = len(df_clean)
        k = len(groups)

        # 1. Check Assumptions
        assumptions = self.check_assumptions(data, variables)

        # 2. Main Analysis: Kruskal-Wallis H Test
        h_stat, p_val = stats.kruskal(*group_series)
        dof = float(k - 1)

        group_summaries = []
        for g_name, g_s in zip(groups, group_series):
            group_summaries.append({
                "name": str(g_name),
                "n": len(g_s),
                "median": float(g_s.median()),
                "iqr": float(stats.iqr(g_s))
            })

        main_results = {
            "test_type": "Kruskal-Wallis Rank Sum Test",
            "h_statistic": float(h_stat),
            "degrees_of_freedom": dof,
            "p_value": float(p_val),
            "k_groups": k,
            "group_summaries": group_summaries
        }

        # 3. Effect Size: Epsilon-Squared (epsilon^2 = H / ((n**2 - 1)/(n + 1))) or simpler H / (n - 1)
        epsilon_squared = float(h_stat / (n_total - 1)) if n_total > 1 else 0.0
        epsilon_squared = max(0.0, min(1.0, epsilon_squared))

        effect_sizes = {
            "epsilon_squared": float(epsilon_squared),
            "interpretation": "Negligible" if epsilon_squared < 0.01 else ("Small" if epsilon_squared < 0.08 else ("Medium" if epsilon_squared < 0.26 else "Large"))
        }

        # 4. Post-Hoc Pairwise Dunn's Test (using Mann-Whitney U pairwise with Bonferroni correction)
        post_hoc_results = None
        if p_val < 0.05 and k >= 3:
            try:
                comparisons = []
                # Compute total number of pairwise comparisons m = k(k-1)/2 for Bonferroni adjustment
                m = k * (k - 1) / 2
                for i in range(k):
                    for j in range(i + 1, k):
                        u_ij, p_raw = stats.mannwhitneyu(group_series[i], group_series[j], alternative='two-sided')
                        p_adj = min(1.0, float(p_raw * m))
                        comparisons.append({
                            "group1": str(groups[i]),
                            "group2": str(groups[j]),
                            "u_statistic": float(u_ij),
                            "p_value_raw": float(p_raw),
                            "p_value_adjusted": p_adj,
                            "significant": bool(p_adj < 0.05)
                        })
                post_hoc_results = {
                    "test_name": "Pairwise Mann-Whitney U Tests (Bonferroni Adjusted Dunn's Equivalent)",
                    "comparisons": comparisons
                }
            except Exception as e:
                post_hoc_results = {"error": f"Failed to compute Dunn post-hoc: {str(e)}"}

        # 5. Code Generation
        r_context = {
            "dep_var": dep_var,
            "group_var": group_var
        }
        r_code = self.generate_r_code(variables, r_context)
        py_code = self._generate_python_code(dep_var, group_var)

        # 6. Plots
        plots = self.generate_plots(df_clean, variables, main_results)

        # 7. Interpretation
        interpretation = self.interpret({"main": main_results, "effect": effect_sizes, "post_hoc": post_hoc_results}, variables)

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
            warnings=[],
            references=[
                "Kruskal, W. H., & Wallis, W. A. (1952). Use of ranks in one-criterion variance analysis. Journal of the American Statistical Association, 47(260), 583-621.",
                "Dunn, O. J. (1964). Multiple comparisons using rank sums. Technometrics, 6(3), 241-252."
            ]
        )

    def generate_r_code(self, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> str:
        options = options or {}
        return CodeGenerator.render_r_template("kruskal.R.j2", options)

    def _generate_python_code(self, dep_var: str, group_var: str) -> str:
        code = f"""import pandas as pd
import scipy.stats as stats

# Prepare clean data
clean_df = data[['{dep_var}', '{group_var}']].dropna()
groups = clean_df['{group_var}'].unique()
group_series = [clean_df[clean_df['{group_var}'] == g]['{dep_var}'] for g in groups]

print(f"Kruskal-Wallis H Test across {{len(groups)}} groups of '{group_var}' (n={{len(clean_df)}})")

# Run Kruskal-Wallis H test
h_stat, p_value = stats.kruskal(*group_series)
print(f"H-Statistic: {{h_stat:.4f}}, p-value: {{p_value:.4f}}")

# Calculate Epsilon-Squared effect size
epsilon_squared = h_stat / (len(clean_df) - 1)
print(f"Epsilon-Squared: {{epsilon_squared:.4f}}")

# Run Pairwise Mann-Whitney U Tests with Bonferroni correction if p < 0.05
if p_value < 0.05 and len(groups) >= 3:
    m = len(groups) * (len(groups) - 1) / 2
    print("\\nBonferroni Adjusted Pairwise Comparisons:")
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            u_ij, p_raw = stats.mannwhitneyu(group_series[i], group_series[j], alternative='two-sided')
            p_adj = min(1.0, p_raw * m)
            print(f"{{groups[i]}} vs {{groups[j]}}: p_adj = {{p_adj:.4f}}")
"""
        return CodeGenerator.format_python_code(self.method_name, code)

    def generate_plots(self, data: pd.DataFrame, variables: Dict[str, Any], results: Dict[str, Any]) -> List[Dict[str, Any]]:
        dep_var = variables["dependent"]
        group_var = variables["grouping"]

        p1 = plotter.plot_boxplot_jitter(
            data=data,
            dep_var=dep_var,
            group_var=group_var,
            title=f"Kruskal-Wallis: Rank & Median Distribution of {dep_var} by {group_var}"
        )

        return [p1]

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
            f"A **{main['test_type']}** was conducted to evaluate differences in **{dep}** across **{main['k_groups']}** independent groups of **{grp}**.",
            f"\n**Main Findings:**",
            f"- There was a {sig_str} difference in rank distributions among the groups ($H({main['degrees_of_freedom']:.0f}) = {main['h_statistic']:.2f}, {p_display}$).",
            f"\n**Effect Size:**",
            f"- The epsilon-squared effect size ($\\epsilon^2$) is **{effect['epsilon_squared']:.3f}**, indicating a **{effect['interpretation'].lower()}** effect."
        ]

        if post_hoc and "comparisons" in post_hoc:
            sig_pairs = [c for c in post_hoc["comparisons"] if c["significant"]]
            lines.append("\n**Post-Hoc Pairwise Comparisons (Bonferroni Adjusted):**")
            if sig_pairs:
                for sp in sig_pairs:
                    lines.append(f"- **{sp['group1']} vs {sp['group2']}**: $U = {sp['u_statistic']:.1f}$, $p_{{adj}} = {sp['p_value_adjusted']:.3f}$")
            else:
                lines.append("- None of the specific pairwise comparisons achieved statistical significance after Bonferroni correction.")

        return "\n".join(lines)
