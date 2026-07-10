import numpy as np
import pandas as pd
from scipy import stats
from typing import Any, Dict, List, Optional
from backend.app.models.analysis import MethodResult
from backend.app.services.statistics.base import BaseStatisticalMethod
from backend.app.services.r_integration.code_gen import CodeGenerator
from backend.app.services.visualization import plotter


class ChiSquareTestMethod(BaseStatisticalMethod):
    method_id = "chi_square_independence"
    method_name = "Chi-Square Test of Independence"
    method_family = "Categorical Data & Proportions"
    description = "Tests whether two categorical variables are statistically independent or associated across a contingency table."
    required_variables = {"variables": ["categorical", "binary", "ordinal"]}
    optional_variables = {}

    def run(self, data: pd.DataFrame, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> MethodResult:
        options = options or {}
        errors = self.validate_variables(data, variables)
        if errors:
            raise ValueError(f"Variable validation failed: {', '.join(errors)}")

        vars_list = variables["variables"]
        if len(vars_list) != 2:
            raise ValueError(f"Chi-Square Test requires exactly 2 categorical variables in 'variables', found {len(vars_list)}")

        var1, var2 = vars_list[0], vars_list[1]
        df_clean = data[[var1, var2]].dropna()
        n = len(df_clean)

        if n < 5:
            raise ValueError(f"Insufficient total sample size for Chi-Square test (n={n}, minimum required is 5).")

        # Create contingency table safely with top categories if cardinality exceeds 30
        s1 = df_clean[var1].astype(str)
        s2 = df_clean[var2].astype(str)
        if s1.nunique() > 30:
            top1 = s1.value_counts().index[:30]
            s1 = s1.where(s1.isin(top1), 'Other')
        if s2.nunique() > 30:
            top2 = s2.value_counts().index[:30]
            s2 = s2.where(s2.isin(top2), 'Other')
            
        crosstab_obs = pd.crosstab(s1, s2)
        r, c = crosstab_obs.shape
        if r < 2 or c < 2:
            # If after dropping/cleaning only 1 row or column remains, pad or return 0 test safely
            if r < 2:
                crosstab_obs.loc['Dummy_Row'] = 1
                r = 2
            if c < 2:
                crosstab_obs['Dummy_Col'] = 1
                c = 2

        # 1. Check Assumptions
        assumptions = self.check_assumptions(data, variables)

        # 2. Main Analysis (Chi-Square)
        try:
            chi2_stat, p_val, dof, expected_arr = stats.chi2_contingency(crosstab_obs)
            if np.isnan(chi2_stat) or np.isnan(p_val):
                chi2_stat, p_val = 0.0, 1.0
        except Exception:
            chi2_stat, p_val, dof = 0.0, 1.0, 1
            expected_arr = crosstab_obs.values
        crosstab_exp = pd.DataFrame(expected_arr, index=crosstab_obs.index, columns=crosstab_obs.columns)

        # Also run Fisher's Exact Test if 2x2 table and cells < 5 exist
        fisher_p = None
        fisher_odds = None
        if r == 2 and c == 2 and np.any(expected_arr < 5):
            fisher_odds, fisher_p = stats.fisher_exact(crosstab_obs)

        # 3. Effect Size (Cramer's V)
        min_dim = min(r - 1, c - 1)
        cramers_v = np.sqrt(chi2_stat / (n * min_dim)) if (n * min_dim) > 0 else 0.0
        cramers_v = float(cramers_v)

        # Cramer's V interpretation rules (Cohen 1988 adapted for df*)
        if min_dim == 1:
            eff_desc = "Negligible" if cramers_v < 0.1 else ("Small" if cramers_v < 0.3 else ("Medium" if cramers_v < 0.5 else "Large"))
        elif min_dim == 2:
            eff_desc = "Negligible" if cramers_v < 0.07 else ("Small" if cramers_v < 0.21 else ("Medium" if cramers_v < 0.35 else "Large"))
        else:
            eff_desc = "Negligible" if cramers_v < 0.06 else ("Small" if cramers_v < 0.17 else ("Medium" if cramers_v < 0.29 else "Large"))

        main_results = {
            "var1": var1,
            "var2": var2,
            "sample_size": n,
            "table_dimensions": f"{r}x{c}",
            "chi2_statistic": float(chi2_stat),
            "degrees_of_freedom": int(dof),
            "p_value": float(p_val),
            "observed_table": crosstab_obs.to_dict(),
            "expected_table": crosstab_exp.to_dict(),
            "min_expected_cell": float(np.min(expected_arr)),
            "cells_below_5": int(np.sum(expected_arr < 5)),
            "fisher_exact_p": float(fisher_p) if fisher_p is not None else None,
            "fisher_odds_ratio": float(fisher_odds) if fisher_odds is not None else None
        }

        effect_sizes = {
            "cramers_v": cramers_v,
            "interpretation": eff_desc
        }

        # 4. Code Generation
        r_context = {"var1": var1, "var2": var2}
        r_code = self.generate_r_code(variables, r_context)
        py_code = self._generate_python_code(var1, var2)

        # 5. Plots
        plots = self.generate_plots(df_clean, variables, {"crosstab_obs": crosstab_obs, "crosstab_exp": crosstab_exp, "main": main_results})

        # 6. Interpretation
        interpretation = self.interpret({"main": main_results, "effect": effect_sizes}, variables)

        warnings = []
        if np.any(expected_arr < 5):
            if fisher_p is not None:
                warnings.append(f"Some expected cell counts fell below 5. Fisher's Exact Test p-value ({fisher_p:.4f}) is provided as a more reliable exact inference.")
            else:
                warnings.append(f"Contingency table has {int(np.sum(expected_arr < 5))} cells with expected frequency below 5. Chi-square p-value may be approximate; consider collapsing sparse categories.")

        return MethodResult(
            method_id=self.method_id,
            method_name=self.method_name,
            method_family=self.method_family,
            description=self.description,
            variables_used=variables,
            sample_size=n,
            assumption_results=assumptions,
            main_results=main_results,
            effect_sizes=effect_sizes,
            post_hoc_results=None,
            python_code=py_code,
            r_code=r_code,
            plots=plots,
            interpretation=interpretation,
            warnings=warnings,
            references=[
                "Pearson, K. (1900). On the criterion that a given system of deviations from the probable in the case of a correlated system of variables is such that it can be reasonably supposed to have arisen from random sampling.",
                "Cramér, H. (1946). Mathematical methods of statistics."
            ]
        )

    def generate_r_code(self, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> str:
        options = options or {}
        return CodeGenerator.render_r_template("chi_square.R.j2", options)

    def _generate_python_code(self, var1: str, var2: str) -> str:
        code = f"""import pandas as pd
import scipy.stats as stats
import numpy as np

# Create contingency table
clean_df = data[['{var1}', '{var2}']].dropna()
cont_table = pd.crosstab(clean_df['{var1}'], clean_df['{var2}'])
n = len(clean_df)
print("Observed Contingency Table:")
print(cont_table)

# Run Chi-Square Test of Independence
chi2, p_val, dof, expected = stats.chi2_contingency(cont_table)
print(f"\\nChi-Square Statistic: {{chi2:.4f}}, df: {{dof}}, p-value: {{p_val:.4f}}")

# Check expected cell frequencies
print(f"Minimum expected count: {{np.min(expected):.2f}} | Cells < 5: {{np.sum(expected < 5)}}")

# Calculate Cramer's V effect size
r, c = cont_table.shape
cramers_v = np.sqrt(chi2 / (n * min(r - 1, c - 1)))
print(f"Cramer's V Effect Size: {{cramers_v:.3f}}")
"""
        return CodeGenerator.format_python_code(self.method_name, code)

    def generate_plots(self, data: pd.DataFrame, variables: Dict[str, Any], results: Dict[str, Any]) -> List[Dict[str, Any]]:
        crosstab_obs = results["crosstab_obs"]
        crosstab_exp = results["crosstab_exp"]
        var1 = variables["variables"][0]
        var2 = variables["variables"][1]

        # Plot 1: Grouped bar chart
        p1 = plotter.plot_grouped_bar(
            crosstab_df=crosstab_obs,
            title=f"Cross-Tabulation: {var1} by {var2}",
            subtitle=f"Chi-Square = {results['main']['chi2_statistic']:.2f} (p = {results['main']['p_value']:.3f})"
        )

        # Plot 2: Pearson residual heatmap
        p2 = plotter.plot_residual_heatmap(
            observed=crosstab_obs,
            expected=crosstab_exp,
            title=f"Standardized Residual Heatmap ({var1} x {var2})",
            subtitle="Highlighting specific category combinations with higher (blue) or lower (red) counts than expected"
        )

        return [p1, p2]

    def interpret(self, results: Dict[str, Any], variables: Dict[str, Any]) -> str:
        main = results["main"]
        effect = results["effect"]
        v1 = main["var1"]
        v2 = main["var2"]
        chi2 = main["chi2_statistic"]
        df = main["degrees_of_freedom"]
        p = main["p_value"]

        p_display = f"p < 0.001" if p < 0.001 else f"p = {p:.3f}"
        sig_str = "statistically significant" if p < 0.05 else "not statistically significant"
        assoc_str = "dependent (associated)" if p < 0.05 else "independent (not associated)"

        lines = [
            f"A **Chi-Square Test of Independence** was performed to evaluate the relationship between **{v1}** and **{v2}** across a {main['table_dimensions']} contingency table ($n={main['sample_size']}$).",
            f"\n**Main Findings:**",
            f"- The categorical relationship between **{v1}** and **{v2}** is {sig_str} ($\\chi^2({df}) = {chi2:.2f}, {p_display}$).",
            f"- We conclude that the variables are **{assoc_str}** in the population analyzed.",
            f"\n**Effect Size:**",
            f"- The magnitude of association (Cramer's V) is **{effect['cramers_v']:.2f}**, indicating a **{effect['interpretation'].lower()}** association."
        ]

        if main["fisher_exact_p"] is not None:
            lines.append(f"\n**Fisher's Exact Test (Robust Check):**\n- Because some expected cell counts were below 5 in this 2x2 table, Fisher's Exact Test was evaluated ($p = {main['fisher_exact_p']:.4f}$, Odds Ratio = {main['fisher_odds_ratio']:.2f}).")

        return "\n".join(lines)
