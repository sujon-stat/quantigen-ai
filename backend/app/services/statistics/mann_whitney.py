import numpy as np
import pandas as pd
from scipy import stats
from typing import Any, Dict, List, Optional
from backend.app.models.analysis import MethodResult
from backend.app.core.exceptions import StatisticalViolationException
from backend.app.services.statistics.base import BaseStatisticalMethod
from backend.app.services.r_integration.code_gen import CodeGenerator
from backend.app.services.visualization import plotter


class MannWhitneyUMethod(BaseStatisticalMethod):
    method_id = "mann_whitney_u"
    method_name = "Mann-Whitney U Test"
    method_family = "Non-Parametric Tests"
    description = "Compares differences between two independent groups when the dependent variable is not normally distributed."
    required_variables = {
        "dependent": ["continuous", "ordinal"],
        "grouping": ["categorical", "binary"]
    }
    optional_variables = {}

    def run(self, data: pd.DataFrame, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> MethodResult:
        options = options or {}
        dep_vars = variables.get("dependent", [])
        if not isinstance(dep_vars, list): dep_vars = [dep_vars]
        grp_vars = variables.get("grouping", [])
        if not isinstance(grp_vars, list): grp_vars = [grp_vars]

        if len(dep_vars) > 1 or len(grp_vars) > 1:
            multi_table = []
            all_summaries = []
            all_assumptions = []
            all_warnings = []
            total_sample = 0
            for d in dep_vars:
                for g in grp_vars:
                    try:
                        sub_res = self.run(data, {"dependent": d, "grouping": g}, options)
                        total_sample = max(total_sample, sub_res.sample_size)
                        all_assumptions.extend(sub_res.assumption_results)
                        all_warnings.extend(sub_res.warnings)
                        if sub_res.main_results.get("group_summaries"):
                            for gs in sub_res.main_results["group_summaries"]:
                                gs_copy = dict(gs)
                                gs_copy["variable"] = d
                                gs_copy["grouping_column"] = g
                                all_summaries.append(gs_copy)
                        multi_table.append({
                            "variable": d,
                            "grouping_column": g,
                            "u_statistic": sub_res.main_results.get("u_statistic", 0.0),
                            "p_value": sub_res.main_results.get("p_value", 1.0),
                            "rank_biserial_r": sub_res.effect_sizes.get("rank_biserial_r", 0.0) if sub_res.effect_sizes else 0.0
                        })
                    except Exception as ex:
                        all_warnings.append(f"Could not compute Mann-Whitney U for {d} by {g}: {str(ex)}")

            return MethodResult(
                method_id=self.method_id,
                method_name=f"Multi-Variable {self.method_name} Table",
                method_family=self.method_family,
                description=f"Multi-variable comparative table across {len(dep_vars)} outcome variable(s) and {len(grp_vars)} grouping variable(s).",
                variables_used=variables,
                sample_size=total_sample,
                assumption_results=all_assumptions[:10],
                main_results={
                    "test_type": "Multi-Variable Mann-Whitney U Table",
                    "multi_variable_table": multi_table,
                    "group_summaries": all_summaries
                },
                effect_sizes={"summary": f"Computed across {len(multi_table)} comparisons."},
                python_code=self._generate_python_code(str(dep_vars[0]), str(grp_vars[0])),
                r_code=self.generate_r_code({"dependent": str(dep_vars[0]), "grouping": str(grp_vars[0])}, {}),
                plots=[],
                interpretation=f"Multi-variable Mann-Whitney comparison table generated successfully for academic manuscript Table 1 covering {len(dep_vars)} dependent variables across {len(grp_vars)} grouping factors.",
                warnings=list(set(all_warnings))
            )

        errors = self.validate_variables(data, variables)
        if errors:
            raise StatisticalViolationException(message=f"Variable validation failed: {', '.join(errors)}", violation_type="variable_validation")

        dep_var = variables["dependent"]
        group_var = variables["grouping"]

        df_clean = data[[dep_var, group_var]].dropna()
        df_clean[group_var] = df_clean[group_var].astype(str)
        group_counts = df_clean[group_var].value_counts()
        valid_groups = group_counts[group_counts >= 1].index.tolist()
        
        if len(valid_groups) < 2:
            raise StatisticalViolationException(
                message=f"Grouping variable '{group_var}' must have at least 2 distinct levels for Mann-Whitney U.",
                violation_type="grouping_levels_violation",
                remedy=f"'{group_var}' has only {len(valid_groups)} group. Please select a categorical column with at least 2 distinct levels."
            )
        
        # Automatically select the 2 most frequent groups if more than 2 exist
        g1_name, g2_name = str(valid_groups[0]), str(valid_groups[1])
        g1 = pd.to_numeric(df_clean[df_clean[group_var] == g1_name][dep_var], errors='coerce').dropna()
        g2 = pd.to_numeric(df_clean[df_clean[group_var] == g2_name][dep_var], errors='coerce').dropna()
        n1, n2 = len(g1), len(g2)
        
        if n1 == 0 or n2 == 0:
            raise StatisticalViolationException(
                message=f"Grouping levels '{g1_name}' or '{g2_name}' have zero numeric values in '{dep_var}'.",
                violation_type="grouping_levels_violation",
                remedy="Ensure the dependent variable contains valid numeric data for the selected groups."
            )
            
        group1_name, group2_name = g1_name, g2_name
        n_total = n1 + n2

        # 1. Check Assumptions
        assumptions = self.check_assumptions(data, variables)

        # 2. Main Analysis: Mann-Whitney U test
        u_stat, p_val = stats.mannwhitneyu(g1, g2, alternative='two-sided')
        if np.isnan(u_stat) or np.isnan(p_val):
            u_stat, p_val = 0.0, 1.0

        main_results = {
            "test_type": "Mann-Whitney U / Wilcoxon Rank-Sum Test",
            "u_statistic": float(u_stat),
            "p_value": float(p_val),
            "group1_summary": {"name": group1_name, "n": n1, "median": float(g1.median()), "iqr": float(stats.iqr(g1))},
            "group2_summary": {"name": group2_name, "n": n2, "median": float(g2.median()), "iqr": float(stats.iqr(g2))}
        }

        # 3. Effect Size: Rank-Biserial Correlation r_rb = 1 - (2U / (n1 * n2))
        r_rb = 1.0 - (2.0 * float(u_stat)) / (n1 * n2) if (n1 * n2) > 0 else 0.0

        effect_sizes = {
            "rank_biserial_r": float(r_rb),
            "interpretation": "Negligible" if abs(r_rb) < 0.1 else ("Small" if abs(r_rb) < 0.3 else ("Medium" if abs(r_rb) < 0.5 else "Large"))
        }

        # 4. Code Generation
        r_context = {
            "dep_var": dep_var,
            "group_var": group_var,
            "conf_level": options.get("conf_level", 0.95)
        }
        r_code = self.generate_r_code(variables, r_context)
        py_code = self._generate_python_code(dep_var, group_var)

        # 5. Plots
        plots = self.generate_plots(df_clean, variables, main_results)

        # 6. Interpretation
        interpretation = self.interpret({"main": main_results, "effect": effect_sizes}, variables)

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
            post_hoc_results=None,
            python_code=py_code,
            r_code=r_code,
            plots=plots,
            interpretation=interpretation,
            warnings=[],
            references=[
                "Mann, H. B., & Whitney, D. R. (1947). On a test of whether one of two random variables is stochastically larger than the other. Annals of Mathematical Statistics, 18(1), 50-60.",
                "Kerby, D. S. (2014). The simple difference formula: An approach to teaching nonparametric correlation. Comprehensive Psychology, 3, 11-IT."
            ]
        )

    def generate_r_code(self, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> str:
        options = options or {}
        return CodeGenerator.render_r_template("mann_whitney.R.j2", options)

    def _generate_python_code(self, dep_var: str, group_var: str) -> str:
        code = f"""import pandas as pd
import scipy.stats as stats

# Prepare clean data
clean_df = data[['{dep_var}', '{group_var}']].dropna()
groups = clean_df['{group_var}'].unique()
g1 = clean_df[clean_df['{group_var}'] == groups[0]]['{dep_var}']
g2 = clean_df[clean_df['{group_var}'] == groups[1]]['{dep_var}']

print(f"Mann-Whitney U Test comparing {{groups[0]}} (n={{len(g1)}}) vs {{groups[1]}} (n={{len(g2)}})")

# Run Mann-Whitney U test
u_stat, p_value = stats.mannwhitneyu(g1, g2, alternative='two-sided')
print(f"U-Statistic: {{u_stat:.4f}}, p-value: {{p_value:.4f}}")

# Calculate Rank-Biserial Correlation r_rb
n1, n2 = len(g1), len(g2)
r_rb = 1.0 - (2.0 * u_stat) / (n1 * n2)
print(f"Rank-Biserial Correlation (r_rb): {{r_rb:.4f}}")
"""
        return CodeGenerator.format_python_code(self.method_name, code)

    def generate_plots(self, data: pd.DataFrame, variables: Dict[str, Any], results: Dict[str, Any]) -> List[Dict[str, Any]]:
        dep_var = variables["dependent"]
        group_var = variables["grouping"]

        p1 = plotter.plot_boxplot_jitter(
            data=data,
            dep_var=dep_var,
            group_var=group_var,
            title=f"Mann-Whitney U: Rank & Median Distribution of {dep_var} by {group_var}"
        )

        return [p1]

    def interpret(self, results: Dict[str, Any], variables: Dict[str, Any]) -> str:
        main = results["main"]
        effect = results["effect"]
        dep = variables["dependent"]
        g1 = main["group1_summary"]
        g2 = main["group2_summary"]

        p_val = main["p_value"]
        sig_str = "statistically significant" if p_val < 0.05 else "not statistically significant"
        p_display = f"p < 0.001" if p_val < 0.001 else f"p = {p_val:.3f}"

        lines = [
            f"A **{main['test_type']}** was conducted to compare rank distributions of **{dep}** between **{g1['name']}** ($n={g1['n']}$) and **{g2['name']}** ($n={g2['n']}$).",
            f"\n**Main Findings:**",
            f"- There was a {sig_str} difference in **{dep}** between the two groups ($U = {main['u_statistic']:.2f}, {p_display}$).",
            f"- **{g1['name']}** had a median of **{g1['median']:.2f}** (IQR = {g1['iqr']:.2f}), while **{g2['name']}** had a median of **{g2['median']:.2f}** (IQR = {g2['iqr']:.2f}).",
            f"\n**Effect Size:**",
            f"- The rank-biserial correlation ($r_{{rb}}$) is **{effect['rank_biserial_r']:.3f}**, indicating a **{effect['interpretation'].lower()}** effect."
        ]

        return "\n".join(lines)
