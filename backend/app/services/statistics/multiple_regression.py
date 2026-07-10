import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson
from statsmodels.stats.outliers_influence import variance_inflation_factor
from typing import Any, Dict, List, Optional
from backend.app.models.analysis import MethodResult
from backend.app.services.statistics.base import BaseStatisticalMethod
from backend.app.services.r_integration.code_gen import CodeGenerator
from backend.app.services.visualization import plotter


class MultipleLinearRegressionMethod(BaseStatisticalMethod):
    method_id = "regression_linear_multiple"
    method_name = "Multiple Linear Regression"
    method_family = "Regression & Modeling"
    description = "Models the linear relationship between a continuous dependent outcome and two or more continuous predictors."
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
        ind_vars = variables["independent"]
        if isinstance(ind_vars, str):
            ind_vars = [ind_vars]
        elif not isinstance(ind_vars, list) or len(ind_vars) < 1:
            raise ValueError("Independent variables must be a list of at least one continuous predictor.")

        df_clean = data[[dep_var] + ind_vars].dropna()
        n = len(df_clean)
        p = len(ind_vars)
        if n <= p + 1:
            raise ValueError(f"Insufficient observations (n={n}) to fit regression with {p} predictors.")

        # 1. Check Assumptions
        assumptions = self.check_assumptions(data, variables)

        # Check Breusch-Pagan for robust SE auto-fix
        bp_passed = True
        for a in assumptions:
            if a.assumption_name == "homoscedasticity":
                bp_passed = a.passed

        # Fit model safely with numeric coercion and fallback
        y = pd.to_numeric(df_clean[dep_var], errors='coerce')
        valid_idx = y.dropna().index
        y = y.loc[valid_idx].astype(float)
        
        X_encoded = pd.get_dummies(df_clean.loc[valid_idx, ind_vars], drop_first=True, dtype=float)
        # Drop zero-variance columns to prevent singular matrix errors
        X_encoded = X_encoded.loc[:, X_encoded.std() > 1e-12]
        if X_encoded.empty:
            # Fallback if all variance dropped: convert raw ind_vars to numeric
            X_encoded = df_clean.loc[valid_idx, ind_vars].apply(pd.to_numeric, errors='coerce').fillna(0.0)
            
        X = sm.add_constant(X_encoded)
        
        cov_type = "HC3" if (not bp_passed or options.get("robust_se")) else "nonrobust"
        try:
            model = sm.OLS(y, X).fit(cov_type=cov_type)
        except Exception:
            model = sm.OLS(y, X).fit(cov_type="nonrobust")

        # Coefficients table
        coefficients = []
        for col_name in X.columns:
            coef_val = float(model.params[col_name])
            std_err = float(model.bse[col_name])
            t_val = float(model.tvalues[col_name])
            p_val = float(model.pvalues[col_name])
            ci_low, ci_high = model.conf_int(alpha=0.05).loc[col_name]
            
            coefficients.append({
                "variable": str(col_name),
                "coefficient": coef_val,
                "std_error": std_err,
                "t_statistic": t_val,
                "p_value": p_val,
                "ci_95_lower": float(ci_low),
                "ci_95_upper": float(ci_high),
                "significant": bool(p_val < 0.05)
            })

        # Multicollinearity VIF
        vif_dict = {}
        if p > 1:
            for i in range(1, X.shape[1]):
                col_name = X.columns[i]
                try:
                    v_val = float(variance_inflation_factor(X.values, i))
                    vif_dict[str(col_name)] = v_val
                except Exception:
                    vif_dict[str(col_name)] = 999.0

        main_results = {
            "test_type": f"Ordinary Least Squares (OLS) Multiple Regression ({cov_type} Standard Errors)",
            "r_squared": float(model.rsquared),
            "adjusted_r_squared": float(model.rsquared_adj),
            "f_statistic": float(model.fvalue) if model.fvalue is not None else 0.0,
            "f_p_value": float(model.f_pvalue) if model.f_pvalue is not None else 0.0,
            "dof_model": float(model.df_model),
            "dof_residual": float(model.df_resid),
            "aic": float(model.aic),
            "bic": float(model.bic),
            "dw_statistic": float(durbin_watson(model.resid)),
            "coefficients": coefficients,
            "vif_diagnostics": vif_dict
        }

        # Effect size: Cohen's f^2 = R^2 / (1 - R^2)
        r2 = float(model.rsquared)
        f_squared = r2 / (1.0 - r2) if r2 < 1.0 else 999.0

        effect_sizes = {
            "cohens_f_squared": float(f_squared),
            "r_squared": r2,
            "interpretation": "Negligible" if f_squared < 0.02 else ("Small" if f_squared < 0.15 else ("Medium" if f_squared < 0.35 else "Large"))
        }

        # Code Generation
        r_context = {
            "dep_var": dep_var,
            "ind_vars": ind_vars
        }
        r_code = self.generate_r_code(variables, r_context)
        py_code = self._generate_python_code(dep_var, ind_vars, cov_type)

        # Plots
        plots = self.generate_plots(df_clean, variables, {"model": model, "fitted": model.fittedvalues, "resid": model.resid})

        # Interpretation
        interpretation = self.interpret({"main": main_results, "effect": effect_sizes}, variables)

        warnings = []
        if not bp_passed or cov_type == "HC3":
            warnings.append("Heteroscedasticity was detected in residual diagnostics. Robust standard errors (HC3) were automatically applied for hypothesis testing.")
        if any(v > 10.0 for v in vif_dict.values()):
            warnings.append("Severe multicollinearity (VIF > 10) detected among one or more independent predictors. Coefficient standard errors may be inflated.")

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
                "Kutner, M. H., Nachtsheim, C. J., Neter, J., & Li, W. (2004). Applied Linear Statistical Models (5th ed.). McGraw-Hill.",
                "Cohen, J. (1988). Statistical power analysis for the behavioral sciences (2nd ed.)."
            ]
        )

    def generate_r_code(self, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> str:
        options = options or {}
        return CodeGenerator.render_r_template("multiple_regression.R.j2", options)

    def _generate_python_code(self, dep_var: str, ind_vars: List[str], cov_type: str) -> str:
        preds_str = "', '".join(ind_vars)
        code = f"""import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Prepare clean data
predictors = ['{preds_str}']
clean_df = data[['{dep_var}'] + predictors].dropna()

y = clean_df['{dep_var}']
X = sm.add_constant(clean_df[predictors])

# Fit OLS model with {cov_type} standard errors
model = sm.OLS(y, X).fit(cov_type='{cov_type}')
print(model.summary())

# Check Variance Inflation Factor (VIF)
if len(predictors) > 1:
    print("\\nVariance Inflation Factors:")
    for i in range(1, X.shape[1]):
        print(f"{{X.columns[i]}}: {{variance_inflation_factor(X.values, i):.2f}}")
"""
        return CodeGenerator.format_python_code(self.method_name, code)

    def generate_plots(self, data: pd.DataFrame, variables: Dict[str, Any], results: Dict[str, Any]) -> List[Dict[str, Any]]:
        dep_var = variables["dependent"]
        ind_vars = variables["independent"]
        if isinstance(ind_vars, str):
            ind_vars = [ind_vars]

        fitted = pd.Series(results["fitted"])
        resid = pd.Series(results["resid"])

        p1 = plotter.plot_residuals_vs_fitted(
            fitted_values=fitted,
            residuals=resid,
            title="Multiple Regression: Residuals vs Fitted Values",
            subtitle="Random scatter around the horizontal zero line indicates linearity and homoscedasticity"
        )

        plots = [p1]
        # If single predictor or primary predictor, also show scatter regression
        if len(ind_vars) >= 1 and ind_vars[0] in data.columns:
            p2 = plotter.plot_scatter_regression(
                data=data,
                x_var=ind_vars[0],
                y_var=dep_var,
                title=f"Bivariate Scatter & OLS Fit: {dep_var} vs {ind_vars[0]}"
            )
            plots.append(p2)

        # Forest plot of coefficients
        try:
            coefs = results.get("main", {}).get("coefficients", [])
            if coefs:
                rows = []
                idx = []
                for c in coefs:
                    if c["variable"].lower() != "intercept":
                        idx.append(c["variable"])
                        rows.append({
                            "coef": c["beta"],
                            "CI_Lower": c["ci_95_lower"],
                            "CI_Upper": c["ci_95_upper"]
                        })
                if rows:
                    params_df = pd.DataFrame(rows, index=idx)
                    p3 = plotter.plot_forest_coefficients(
                        params_df=params_df,
                        title=f"Multiple Regression: Forest Plot of Coefficients Beta ({dep_var})"
                    )
                    plots.append(p3)
        except Exception:
            pass

        return plots

    def interpret(self, results: Dict[str, Any], variables: Dict[str, Any]) -> str:
        main = results["main"]
        effect = results["effect"]
        dep = variables["dependent"]

        p_val = main["f_p_value"]
        sig_str = "statistically significant" if p_val < 0.05 else "not statistically significant"
        p_display = f"p < 0.001" if p_val < 0.001 else f"p = {p_val:.3f}"

        lines = [
            f"A **{main['test_type']}** was fitted to predict **{dep}** from **{main['dof_model']:.0f}** predictors ($n={results.get('sample_size', 'N')}$).",
            f"\n**Model Summary:**",
            f"- The overall regression model was {sig_str} ($F({main['dof_model']:.0f}, {main['dof_residual']:.0f}) = {main['f_statistic']:.2f}, {p_display}$).",
            f"- The model accounts for **{main['r_squared']*100:.1f}%** of the variance in {dep} (Adjusted $R^2 = {main['adjusted_r_squared']:.3f}$).",
            f"\n**Significant Predictors:**"
        ]

        sig_coefs = [c for c in main["coefficients"] if c["variable"] != "const" and c["significant"]]
        if sig_coefs:
            for sc in sig_coefs:
                lines.append(f"- **{sc['variable']}**: $\\beta = {sc['coefficient']:.3f}$ ($t = {sc['t_statistic']:.2f}, p = {sc['p_value']:.3f}$, 95% CI [{sc['ci_95_lower']:.3f}, {sc['ci_95_upper']:.3f}]).")
        else:
            lines.append("- None of the individual predictor slopes reached statistical significance after controlling for the other variables in the model.")

        return "\n".join(lines)
