import numpy as np
import pandas as pd
from scipy import stats
from typing import Any, Dict, List, Optional
from backend.app.models.analysis import MethodResult
from backend.app.services.statistics.base import BaseStatisticalMethod
from backend.app.services.r_integration.code_gen import CodeGenerator
from backend.app.services.visualization import plotter


class SimpleLinearRegressionMethod(BaseStatisticalMethod):
    method_id = "regression_linear_simple"
    method_name = "Simple Linear Regression"
    method_family = "Regression & Modeling"
    description = "Models the linear dependency of a continuous outcome variable (Y) on a single continuous predictor variable (X)."
    required_variables = {
        "dependent": ["continuous"],
        "independent": ["continuous"]
    }
    optional_variables = {}

    def run(self, data: pd.DataFrame, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> MethodResult:
        options = options or {}
        errors = self.validate_variables(data, variables)
        if errors:
            raise ValueError(f"Variable validation failed: {', '.join(errors)}")

        dep_var = variables["dependent"]
        ind_var = variables["independent"]

        df_clean = data[[dep_var, ind_var]].copy()
        df_clean[dep_var] = pd.to_numeric(df_clean[dep_var], errors='coerce')
        df_clean[ind_var] = pd.to_numeric(df_clean[ind_var], errors='coerce')
        df_clean = df_clean.dropna()
        n = len(df_clean)

        if n < 3:
            raise ValueError(f"Insufficient sample size for Simple Linear Regression (n={n}, minimum required is 3).")

        # 1. Check Assumptions
        assumptions = self.check_assumptions(data, variables)

        # Check Breusch-Pagan homoscedasticity outcome for robust SE auto-fix
        bp_passed = True
        for a in assumptions:
            if a.assumption_name == "homoscedasticity":
                bp_passed = a.passed

        use_robust = options.get("robust_se", not bp_passed)

        # 2. Main Analysis (OLS matrix & inference)
        x_raw = df_clean[ind_var].values.astype(float)
        y = df_clean[dep_var].values.astype(float)
        X = np.column_stack([np.ones(n), x_raw])  # Design matrix with intercept

        # OLS beta coefficients using pseudo-inverse for complete numerical stability: (X'X)^(-1) X'Y
        xtx_inv = np.linalg.pinv(X.T @ X)
        beta = xtx_inv @ X.T @ y
        intercept, slope = float(beta[0]), float(beta[1])

        # Fitted values and residuals
        y_pred = X @ beta
        residuals = y - y_pred

        # Sum of squares
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        ss_res = float(np.sum(residuals ** 2))
        ss_reg = ss_tot - ss_res
        r_squared = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0
        adj_r_squared = float(1.0 - (1.0 - r_squared) * (n - 1) / (n - 2))

        # Residual variance (MSE)
        mse = ss_res / (n - 2)
        rmse = float(np.sqrt(mse))

        # Standard Errors calculation (Standard OLS vs HC3 Robust)
        if use_robust:
            # HC3 diagonal weighting: e_i^2 / (1 - h_ii)^2
            H = X @ xtx_inv @ X.T
            h_ii = np.diag(H)
            hc3_weights = (residuals ** 2) / ((1.0 - h_ii) ** 2)
            omega = np.diag(hc3_weights)
            vcov = xtx_inv @ (X.T @ omega @ X) @ xtx_inv
            se_beta = np.sqrt(np.diag(vcov))
            se_intercept, se_slope = float(se_beta[0]), float(se_beta[1])
            se_type = "HC3 Robust Standard Errors (Heteroscedasticity Adjusted)"
        else:
            vcov = mse * xtx_inv
            se_beta = np.sqrt(np.diag(vcov))
            se_intercept, se_slope = float(se_beta[0]), float(se_beta[1])
            se_type = "Standard OLS Standard Errors"

        # t-statistics and p-values
        t_intercept = intercept / se_intercept if se_intercept > 0 else 0.0
        p_intercept = float(2.0 * (1.0 - stats.t.cdf(abs(t_intercept), df=n - 2)))

        t_slope = slope / se_slope if se_slope > 0 else 0.0
        p_slope = float(2.0 * (1.0 - stats.t.cdf(abs(t_slope), df=n - 2)))

        # 95% CIs
        t_crit = stats.t.ppf(0.975, df=n - 2)
        ci_intercept = [float(intercept - t_crit * se_intercept), float(intercept + t_crit * se_intercept)]
        ci_slope = [float(slope - t_crit * se_slope), float(slope + t_crit * se_slope)]

        # Overall model F-statistic
        f_stat = float((ss_reg / 1.0) / mse) if mse > 0 else 0.0
        p_model = float(1.0 - stats.f.cdf(f_stat, dfn=1, dfd=n - 2))

        main_results = {
            "dependent_variable": dep_var,
            "independent_variable": ind_var,
            "sample_size": n,
            "se_method_used": se_type,
            "r_squared": r_squared,
            "adjusted_r_squared": adj_r_squared,
            "rmse": rmse,
            "f_statistic": f_stat,
            "f_p_value": p_model,
            "degrees_of_freedom_model": 1,
            "degrees_of_freedom_residual": int(n - 2),
            "coefficients": {
                "intercept": {
                    "estimate": intercept,
                    "std_error": se_intercept,
                    "t_statistic": float(t_intercept),
                    "p_value": p_intercept,
                    "ci_95_lower": ci_intercept[0],
                    "ci_95_upper": ci_intercept[1]
                },
                "slope": {
                    "estimate": slope,
                    "std_error": se_slope,
                    "t_statistic": float(t_slope),
                    "p_value": p_slope,
                    "ci_95_lower": ci_slope[0],
                    "ci_95_upper": ci_slope[1]
                }
            },
            "anova_table": {
                "regression": {"sum_squares": ss_reg, "df": 1, "mean_square": ss_reg, "f_stat": f_stat, "p_val": p_model},
                "residual": {"sum_squares": ss_res, "df": int(n - 2), "mean_square": float(mse)},
                "total": {"sum_squares": ss_tot, "df": int(n - 1)}
            }
        }

        # 3. Effect Size
        # Standardized beta (in simple regression, beta_standardized == Pearson r)
        std_beta = slope * (np.std(x_raw, ddof=1) / np.std(y, ddof=1))
        effect_sizes = {
            "r_squared": r_squared,
            "standardized_beta": float(std_beta),
            "interpretation": "Weak" if r_squared < 0.13 else ("Moderate" if r_squared < 0.26 else "Strong")
        }

        # 4. Code Generation
        r_context = {
            "dep_var": dep_var,
            "ind_var": ind_var,
            "use_robust": "TRUE" if use_robust else "FALSE"
        }
        r_code = self.generate_r_code(variables, r_context)
        py_code = self._generate_python_code(dep_var, ind_var, use_robust)

        # 5. Plots
        plots = self.generate_plots(df_clean, variables, {"main": main_results, "fitted": pd.Series(y_pred), "residuals": pd.Series(residuals)})

        # 6. Interpretation
        interpretation = self.interpret({"main": main_results, "effect": effect_sizes}, variables)

        warnings = []
        if use_robust and not bp_passed:
            warnings.append("Breusch-Pagan test detected heteroscedasticity (non-constant error variance). Robust HC3 standard errors were automatically applied to ensure valid confidence intervals and p-values without data distortion.")

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
                "Galton, F. (1886). Regression towards mediocrity in hereditary stature.",
                "MacKinnon, J. G., & White, H. (1985). Some heteroskedasticity-consistent covariance matrix estimators with improved finite sample properties."
            ]
        )

    def generate_r_code(self, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> str:
        options = options or {}
        return CodeGenerator.render_r_template("regression.R.j2", options)

    def _generate_python_code(self, dep_var: str, ind_var: str, use_robust: bool) -> str:
        code = f"""import pandas as pd
import statsmodels.api as sm
import statsmodels.stats.diagnostic as diag

# Prepare model variables
clean_df = data[['{dep_var}', '{ind_var}']].dropna()
y = clean_df['{dep_var}']
X = sm.add_constant(clean_df['{ind_var}'])

# Assumption check: Breusch-Pagan homoscedasticity test
ols_temp = sm.OLS(y, X).fit()
bp_stat, bp_p, _, _ = diag.het_breuschpagan(ols_temp.resid, X)
print(f"Breusch-Pagan homoscedasticity test: p = {{bp_p:.4f}}")

# Fit OLS Regression Model (cov_type={'HC3' if use_robust else 'nonrobust'})
model = sm.OLS(y, X).fit(cov_type='{'HC3' if use_robust else 'nonrobust'}')
print(model.summary())
"""
        return CodeGenerator.format_python_code(self.method_name, code)

    def generate_plots(self, data: pd.DataFrame, variables: Dict[str, Any], results: Dict[str, Any]) -> List[Dict[str, Any]]:
        dep_var = variables["dependent"]
        ind_var = variables["independent"]

        # Plot 1: Regression line with 95% confidence band
        p1 = plotter.plot_scatter_regression(
            data=data,
            x_var=ind_var,
            y_var=dep_var,
            title=f"Simple Linear Regression: {dep_var} vs {ind_var}",
            subtitle=f"R-Squared = {results['main']['r_squared']:.3f} | Slope = {results['main']['coefficients']['slope']['estimate']:.2f} (p = {results['main']['coefficients']['slope']['p_value']:.3f})"
        )

        # Plot 2: Residuals vs Fitted plot
        p2 = plotter.plot_residuals_vs_fitted(
            fitted_values=results["fitted"],
            residuals=results["residuals"],
            title="Residuals vs Fitted Diagnostics",
            subtitle="Evaluating linearity and homoscedasticity assumptions across predicted range"
        )

        return [p1, p2]

    def interpret(self, results: Dict[str, Any], variables: Dict[str, Any]) -> str:
        main = results["main"]
        effect = results["effect"]
        dep = main["dependent_variable"]
        ind = main["independent_variable"]
        slope_obj = main["coefficients"]["slope"]
        intercept_obj = main["coefficients"]["intercept"]

        p_slope = slope_obj["p_value"]
        p_display = f"p < 0.001" if p_slope < 0.001 else f"p = {p_slope:.3f}"
        sig_str = "statistically significant" if p_slope < 0.05 else "not statistically significant"

        direction = "increase" if slope_obj["estimate"] > 0 else "decrease"
        abs_slope = abs(slope_obj["estimate"])

        lines = [
            f"A **Simple Linear Regression** was conducted to examine how **{ind}** predicts **{dep}** ($n={main['sample_size']}$), utilizing **{main['se_method_used']}**.",
            f"\n**Overall Model Fit:**",
            f"- The overall regression model is statistically significant ($F(1, {main['degrees_of_freedom_residual']}) = {main['f_statistic']:.2f}, p = {main['f_p_value']:.4f}$).",
            f"- The model explains **{main['r_squared']*100:.1f}%** ($R^2 = {main['r_squared']:.3f}$, Adjusted $R^2 = {main['adjusted_r_squared']:.3f}$) of the variance in **{dep}**, which represents a **{effect['interpretation'].lower()}** effect.",
            f"\n**Coefficients & Prediction:**",
            f"- **{ind} (Slope)**: The regression coefficient is {sig_str} ($t({main['degrees_of_freedom_residual']}) = {slope_obj['t_statistic']:.2f}, {p_display}$).",
            f"- For every 1-unit increase in **{ind}**, **{dep}** is predicted to {direction} by **{abs_slope:.2f} units** (95% CI: [{slope_obj['ci_95_lower']:.2f}, {slope_obj['ci_95_upper']:.2f}]).",
            f"- **Intercept**: When **{ind}** is 0, the expected baseline value of **{dep}** is **{intercept_obj['estimate']:.2f}** (SE = {intercept_obj['std_error']:.2f})."
        ]

        return "\n".join(lines)
