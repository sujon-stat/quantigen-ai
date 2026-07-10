import numpy as np
import pandas as pd
from scipy import stats
from typing import Any, Dict, List, Optional
from backend.app.models.analysis import MethodResult
from backend.app.models.assumptions import Severity
from backend.app.core.exceptions import StatisticalViolationException
from backend.app.services.statistics.base import BaseStatisticalMethod
from backend.app.services.r_integration.code_gen import CodeGenerator
from backend.app.services.visualization import plotter


class IndependentSamplesTTestMethod(BaseStatisticalMethod):
    method_id = "ttest_independent"
    method_name = "Independent Samples T-Test"
    method_family = "T-Tests & Group Comparisons"
    description = "Compares the means of a continuous dependent variable across two distinct independent groups."
    required_variables = {
        "dependent": ["continuous"],
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
                            "t_statistic": sub_res.main_results.get("t_statistic", 0.0),
                            "p_value": sub_res.main_results.get("p_value", 1.0),
                            "degrees_of_freedom": sub_res.main_results.get("degrees_of_freedom", 0),
                            "cohens_d": sub_res.effect_sizes.get("cohens_d", 0.0) if sub_res.effect_sizes else 0.0,
                            "mean_difference": sub_res.main_results.get("mean_difference", 0.0)
                        })
                    except Exception as ex:
                        all_warnings.append(f"Could not compute T-Test for {d} by {g}: {str(ex)}")

            return MethodResult(
                method_id=self.method_id,
                method_name=f"Multi-Variable {self.method_name} Table",
                method_family=self.method_family,
                description=f"Multi-variable comparative table across {len(dep_vars)} outcome variable(s) and {len(grp_vars)} grouping variable(s).",
                variables_used=variables,
                sample_size=total_sample,
                assumption_results=all_assumptions[:10],
                main_results={
                    "test_type": "Multi-Variable Independent T-Test Table",
                    "multi_variable_table": multi_table,
                    "group_summaries": all_summaries
                },
                effect_sizes={"summary": f"Computed across {len(multi_table)} comparisons."},
                python_code=self._generate_python_code(str(dep_vars[0]), str(grp_vars[0]), True),
                r_code=self.generate_r_code({"dependent": str(dep_vars[0]), "grouping": str(grp_vars[0])}, {}),
                plots=[],
                interpretation=f"Multi-variable T-Test comparison table generated successfully for academic manuscript Table 1 covering {len(dep_vars)} dependent variables across {len(grp_vars)} grouping factors.",
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
                message=f"Grouping variable '{group_var}' must have at least 2 distinct categories for T-Test.",
                violation_type="grouping_levels_violation",
                remedy=f"'{group_var}' has only {len(valid_groups)} group. Please select a categorical column with at least 2 distinct groups."
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

        # Determine equal variance or Welch's auto-fix
        levene_passed = True
        for a in assumptions:
            if a.assumption_name == "homogeneity_variance":
                levene_passed = a.passed
                
        if "equal_var" in options:
            equal_var = bool(options["equal_var"])
        else:
            equal_var = levene_passed

        # 2. Main Analysis (T-Test)
        s1_sq, s2_sq = float(g1.var(ddof=1)) if n1 > 1 else 1e-6, float(g2.var(ddof=1)) if n2 > 1 else 1e-6
        if s1_sq < 1e-12 and s2_sq < 1e-12:
            equal_var = True
            
        t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=equal_var)
        if np.isnan(t_stat) or np.isnan(p_val):
            t_stat, p_val = 0.0, 1.0
        
        # Degrees of freedom calculation
        if equal_var:
            dof = float(max(1, n1 + n2 - 2))
        else:
            # Welch-Satterthwaite equation
            denom = (((s1_sq/n1)**2)/(max(1, n1-1)) + ((s2_sq/n2)**2)/(max(1, n2-1)))
            dof = float(((s1_sq/n1 + s2_sq/n2)**2) / denom) if denom > 0 else float(max(1, n1 + n2 - 2))

        # Mean differences and 95% CI of mean difference
        mean_diff = float(g1.mean() - g2.mean())
        if equal_var:
            se_diff = float(np.sqrt((((max(1, n1-1)*s1_sq + max(1, n2-1)*s2_sq)/max(1, n1+n2-2))) * (1/n1 + 1/n2)))
        else:
            se_diff = float(np.sqrt((s1_sq/n1) + (s2_sq/n2)))
        t_crit = stats.t.ppf(0.975, df=dof)
        ci_lower = mean_diff - t_crit * se_diff
        ci_upper = mean_diff + t_crit * se_diff

        main_results = {
            "test_type": "Standard Student's T-Test" if equal_var else "Welch's T-Test (Unequal Variances Adjusted)",
            "t_statistic": float(t_stat),
            "degrees_of_freedom": float(dof),
            "p_value": float(p_val),
            "mean_difference": mean_diff,
            "se_difference": se_diff,
            "ci_95_lower": ci_lower,
            "ci_95_upper": ci_upper,
            "group1_summary": {"name": group1_name, "n": n1, "mean": float(g1.mean()), "std": float(g1.std())},
            "group2_summary": {"name": group2_name, "n": n2, "mean": float(g2.mean()), "std": float(g2.std())}
        }

        # 3. Effect Size (Cohen's d with 95% CI)
        pooled_std = np.sqrt(((n1 - 1)*g1.var(ddof=1) + (n2 - 1)*g2.var(ddof=1)) / (n1 + n2 - 2))
        cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0.0
        
        # Approximate SE of Cohen's d
        se_d = np.sqrt((n1 + n2)/(n1 * n2) + (cohens_d**2)/(2 * (n1 + n2)))
        d_ci_lower = float(cohens_d - 1.96 * se_d)
        d_ci_upper = float(cohens_d + 1.96 * se_d)

        effect_sizes = {
            "cohens_d": float(cohens_d),
            "d_ci_lower": d_ci_lower,
            "d_ci_upper": d_ci_upper,
            "interpretation": "Negligible" if abs(cohens_d) < 0.2 else ("Small" if abs(cohens_d) < 0.5 else ("Medium" if abs(cohens_d) < 0.8 else "Large"))
        }

        # 4. Code Generation
        r_context = {
            "dep_var": dep_var,
            "group_var": group_var,
            "var_equal": "TRUE" if equal_var else "FALSE",
            "conf_level": options.get("conf_level", 0.95)
        }
        r_code = self.generate_r_code(variables, r_context)
        py_code = self._generate_python_code(dep_var, group_var, equal_var)

        # 5. Plots
        plots = self.generate_plots(df_clean, variables, main_results)

        # 6. Interpretation
        interpretation = self.interpret({"main": main_results, "effect": effect_sizes}, variables)

        warnings = []
        if not equal_var:
            warnings.append("Levene's test indicated unequal variances across groups. Welch's t-test correction was automatically applied to ensure accurate degrees of freedom and standard error.")

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
            warnings=warnings,
            references=[
                "Welch, B. L. (1947). The generalization of 'Student's' problem when several different population variances are involved.",
                "Cohen, J. (1988). Statistical power analysis for the behavioral sciences (2nd ed.)."
            ]
        )

    def generate_r_code(self, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> str:
        options = options or {}
        return CodeGenerator.render_r_template("ttest.R.j2", options)

    def _generate_python_code(self, dep_var: str, group_var: str, equal_var: bool) -> str:
        code = f"""import pandas as pd
import scipy.stats as stats
import numpy as np

# Prepare clean data
clean_df = data[['{dep_var}', '{group_var}']].dropna()
groups = clean_df['{group_var}'].unique()
g1 = clean_df[clean_df['{group_var}'] == groups[0]]['{dep_var}']
g2 = clean_df[clean_df['{group_var}'] == groups[1]]['{dep_var}']

print(f"Comparing {{groups[0]}} (n={{len(g1)}}) vs {{groups[1]}} (n={{len(g2)}})")

# Assumption check: Levene's test for homogeneity of variance
levene_stat, levene_p = stats.levene(g1, g2, center='median')
print(f"Levene's test: F = {{levene_stat:.4f}}, p = {{levene_p:.4f}}")

# Run Independent Samples T-Test (equal_var={equal_var})
t_stat, p_value = stats.ttest_ind(g1, g2, equal_var={equal_var})
print(f"T-Statistic: {{t_stat:.4f}}, p-value: {{p_value:.4f}}")

# Calculate Cohen's d effect size
n1, n2 = len(g1), len(g2)
pooled_std = np.sqrt(((n1 - 1)*g1.var(ddof=1) + (n2 - 1)*g2.var(ddof=1)) / (n1 + n2 - 2))
cohens_d = (g1.mean() - g2.mean()) / pooled_std
print(f"Cohen's d: {{cohens_d:.3f}}")
"""
        return CodeGenerator.format_python_code(self.method_name, code)

    def generate_plots(self, data: pd.DataFrame, variables: Dict[str, Any], results: Dict[str, Any]) -> List[Dict[str, Any]]:
        dep_var = variables["dependent"]
        group_var = variables["grouping"]

        # Plot 1: Boxplot with Jitter and mean diamond
        p1 = plotter.plot_boxplot_jitter(
            data=data,
            dep_var=dep_var,
            group_var=group_var,
            title=f"Comparison of {dep_var} by {group_var}"
        )

        # Plot 2: Q-Q plot per group
        groups = data[group_var].unique()
        series_dict = {str(grp): data[data[group_var] == grp][dep_var] for grp in groups}
        p2 = plotter.plot_qq_normality(
            series_dict=series_dict,
            title=f"Normality Q-Q Plot of {dep_var} per Group",
            subtitle="Points adhering closely to the dashed diagonal line indicate normality"
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
        dep = variables["dependent"]
        grp = variables["grouping"]
        g1 = main["group1_summary"]
        g2 = main["group2_summary"]

        p_val = main["p_value"]
        sig_str = "statistically significant" if p_val < 0.05 else "not statistically significant"
        p_display = f"p < 0.001" if p_val < 0.001 else f"p = {p_val:.3f}"

        lines = [
            f"An **{main['test_type']}** was conducted to compare **{dep}** between **{g1['name']}** (n = {g1['n']:,}) and **{g2['name']}** (n = {g2['n']:,}).",
            f"\n**Main Findings:**",
            f"- There was a {sig_str} difference in mean **{dep}** between the groups (t({main['degrees_of_freedom']:.2f}) = {main['t_statistic']:.2f}, {p_display}).",
            f"- **{g1['name']}** had an average {dep} of **{g1['mean']:.2f}** (SD = {g1['std']:.2f}), compared to **{g2['mean']:.2f}** (SD = {g2['std']:.2f}) for **{g2['name']}**.",
            f"- The estimated mean difference is **{main['mean_difference']:.2f}** (95% CI: [{main['ci_95_lower']:.2f}, {main['ci_95_upper']:.2f}]).",
            f"\n**Effect Size:**",
            f"- The standardized effect size (Cohen's d) is **{effect['cohens_d']:.2f}** (95% CI: [{effect['d_ci_lower']:.2f}, {effect['d_ci_upper']:.2f}]), which represents a **{effect['interpretation'].lower()}** practical effect."
        ]

        return "\n".join(lines)
