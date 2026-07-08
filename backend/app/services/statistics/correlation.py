import numpy as np
import pandas as pd
from scipy import stats
from typing import Any, Dict, List, Optional
from backend.app.models.analysis import MethodResult
from backend.app.services.statistics.base import BaseStatisticalMethod
from backend.app.services.r_integration.code_gen import CodeGenerator
from backend.app.services.visualization import plotter


class PearsonCorrelationMethod(BaseStatisticalMethod):
    method_id = "correlation_pearson"
    method_name = "Pearson Correlation"
    method_family = "Relationships & Associations"
    description = "Measures the strength and direction of the linear relationship between two continuous numeric variables."
    required_variables = {"variables": ["continuous"]}
    optional_variables = {}

    def run(self, data: pd.DataFrame, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> MethodResult:
        options = options or {}
        errors = self.validate_variables(data, variables)
        if errors:
            raise ValueError(f"Variable validation failed: {', '.join(errors)}")

        vars_list = variables["variables"]
        if len(vars_list) != 2:
            raise ValueError(f"Pearson Correlation requires exactly 2 continuous variables in 'variables', found {len(vars_list)}")

        var1, var2 = vars_list[0], vars_list[1]
        df_clean = data[[var1, var2]].dropna()
        n = len(df_clean)

        if n < 5:
            raise ValueError(f"Insufficient paired sample size for Pearson correlation (n={n}, minimum required is 5).")

        # 1. Check Assumptions
        assumptions = self.check_assumptions(data, variables)

        # 2. Main Analysis (Pearson r and exact p-value)
        r_val, p_val = stats.pearsonr(df_clean[var1], df_clean[var2])
        r_val = float(r_val)
        p_val = float(p_val)

        # Calculate Fisher's Z transformation for 95% CI of r
        if abs(r_val) == 1.0 or n <= 3:
            ci_lower, ci_upper = r_val, r_val
        else:
            z_r = np.arctanh(r_val)
            se_z = 1.0 / np.sqrt(n - 3)
            z_crit = stats.norm.ppf(0.975)
            ci_lower = float(np.tanh(z_r - z_crit * se_z))
            ci_upper = float(np.tanh(z_r + z_crit * se_z))

        # Also calculate Spearman rho as a robustness comparison
        rho_val, rho_p = stats.spearmanr(df_clean[var1], df_clean[var2])
        rho_val = float(rho_val)

        main_results = {
            "var1": var1,
            "var2": var2,
            "sample_size": n,
            "pearson_r": r_val,
            "p_value": p_val,
            "ci_95_lower": ci_lower,
            "ci_95_upper": ci_upper,
            "r_squared": float(r_val ** 2),
            "spearman_rho": rho_val,
            "spearman_p": float(rho_p)
        }

        # 3. Effect Size
        effect_sizes = {
            "r_value": r_val,
            "r_squared": float(r_val ** 2),
            "interpretation": "Negligible" if abs(r_val) < 0.1 else ("Small" if abs(r_val) < 0.3 else ("Medium" if abs(r_val) < 0.5 else "Large"))
        }

        # 4. Code Generation
        r_context = {
            "var1": var1,
            "var2": var2,
            "conf_level": options.get("conf_level", 0.95)
        }
        r_code = self.generate_r_code(variables, r_context)
        py_code = self._generate_python_code(var1, var2)

        # 5. Plots
        plots = self.generate_plots(df_clean, variables, main_results)

        # 6. Interpretation
        interpretation = self.interpret({"main": main_results, "effect": effect_sizes}, variables)

        warnings = []
        if abs(r_val - rho_val) > 0.2:
            warnings.append(f"Noticeable discrepancy between Pearson r ({r_val:.2f}) and Spearman rho ({rho_val:.2f}), indicating potential non-linearity or extreme outliers.")

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
                "Pearson, K. (1895). Note on regression and inheritance in the case of two parents.",
                "Fisher, R. A. (1915). Frequency distribution of the values of the correlation coefficient in samples from an indefinitely large population."
            ]
        )

    def generate_r_code(self, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> str:
        options = options or {}
        return CodeGenerator.render_r_template("correlation.R.j2", options)

    def _generate_python_code(self, var1: str, var2: str) -> str:
        code = f"""import pandas as pd
import scipy.stats as stats
import numpy as np

# Prepare paired data
paired_data = data[['{var1}', '{var2}']].dropna()
n = len(paired_data)
print(f"Analyzing paired correlation between '{var1}' and '{var2}' (n={{n}})")

# Assumption check: Bivariate normality (Shapiro-Wilk on both series)
w1, p1 = stats.shapiro(paired_data['{var1}'])
w2, p2 = stats.shapiro(paired_data['{var2}'])
print(f"Shapiro-Wilk '{var1}': p = {{p1:.4f}} | '{var2}': p = {{p2:.4f}}")

# Run Pearson Correlation
r_val, p_val = stats.pearsonr(paired_data['{var1}'], paired_data['{var2}'])
print(f"Pearson Correlation (r): {{r_val:.4f}}, p-value: {{p_val:.4f}}")

# Calculate Fisher Z 95% Confidence Interval for r
z = np.arctanh(r_val)
se_z = 1.0 / np.sqrt(n - 3)
ci_lower = np.tanh(z - 1.96 * se_z)
ci_upper = np.tanh(z + 1.96 * se_z)
print(f"95% CI: [{{ci_lower:.4f}}, {{ci_upper:.4f}}], R-Squared: {{r_val**2:.4f}}")
"""
        return CodeGenerator.format_python_code(self.method_name, code)

    def generate_plots(self, data: pd.DataFrame, variables: Dict[str, Any], results: Dict[str, Any]) -> List[Dict[str, Any]]:
        var1 = variables["variables"][0]
        var2 = variables["variables"][1]

        # Plot 1: Scatter plot with OLS line and 95% CI band
        p1 = plotter.plot_scatter_regression(
            data=data,
            x_var=var1,
            y_var=var2,
            title=f"Relationship between {var1} and {var2}",
            subtitle=f"Pearson r = {results['pearson_r']:.2f} (p = {results['p_value']:.3f})"
        )

        # Plot 2: Q-Q plots for both variables
        series_dict = {var1: data[var1], var2: data[var2]}
        p2 = plotter.plot_qq_normality(
            series_dict=series_dict,
            title=f"Normality Diagnostics for {var1} and {var2}",
            subtitle="Evaluating univariate normality of correlated variables"
        )

        return [p1, p2]

    def interpret(self, results: Dict[str, Any], variables: Dict[str, Any]) -> str:
        main = results["main"]
        effect = results["effect"]
        v1 = main["var1"]
        v2 = main["var2"]
        r = main["pearson_r"]
        p = main["p_value"]

        direction = "positive" if r > 0 else "negative"
        p_display = f"p < 0.001" if p < 0.001 else f"p = {p:.3f}"
        sig_str = "statistically significant" if p < 0.05 else "not statistically significant"

        lines = [
            f"A **Pearson Correlation** was conducted to examine the linear relationship between **{v1}** and **{v2}** across $n={main['sample_size']}$ paired observations.",
            f"\n**Main Findings:**",
            f"- There is a **{effect['interpretation'].lower()} {direction}** linear correlation between **{v1}** and **{v2}** ($r = {r:.2f}, {p_display}$), which is {sig_str}.",
            f"- The 95% confidence interval for the population correlation coefficient is **[{main['ci_95_lower']:.2f}, {main['ci_95_upper']:.2f}]**.",
            f"- The coefficient of determination ($r^2 = {main['r_squared']:.2f}$) indicates that approximately **{main['r_squared']*100:.1f}%** of the variance in **{v2}** is linearly explained by **{v1}**.",
            f"\n**Non-Parametric Comparison:**",
            f"- Spearman's rank-order correlation yielded $\\rho = {main['spearman_rho']:.2f}$ ($p = {main['spearman_p']:.3f}$), confirming the overall direction and magnitude of association without assuming linearity or normality."
        ]

        return "\n".join(lines)
