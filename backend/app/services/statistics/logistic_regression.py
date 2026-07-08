import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from typing import Any, Dict, List, Optional
from backend.app.models.analysis import MethodResult
from backend.app.services.statistics.base import BaseStatisticalMethod
from backend.app.services.r_integration.code_gen import CodeGenerator
from backend.app.services.visualization import plotter


class LogisticRegressionMethod(BaseStatisticalMethod):
    method_id = "regression_logistic"
    method_name = "Binary Logistic Regression"
    method_family = "Categorical & Classification Modeling"
    description = "Models the log-odds and predicted probability of a binary (0/1) outcome based on continuous or categorical predictors."
    required_variables = {
        "dependent": ["binary", "categorical"],
        "independent": ["continuous", "categorical"]
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
            raise ValueError("Independent variables must be a list of at least one predictor.")

        df_clean = data[[dep_var] + ind_vars].dropna().copy()
        n = len(df_clean)
        p = len(ind_vars)
        if n <= p + 1:
            raise ValueError(f"Insufficient observations (n={n}) to fit logistic regression with {p} predictors.")

        # Ensure dependent variable is binary (0/1 numeric)
        unique_vals = sorted(df_clean[dep_var].unique())
        if len(unique_vals) != 2:
            raise ValueError(f"Dependent variable '{dep_var}' must have exactly 2 distinct levels, found {len(unique_vals)}: {unique_vals}")

        # Map to 0 and 1
        mapping = {unique_vals[0]: 0, unique_vals[1]: 1}
        df_clean["_y_binary"] = df_clean[dep_var].map(mapping)

        # 1. Check Assumptions
        assumptions = self.check_assumptions(data, variables)

        # Fit Logit model
        y = df_clean["_y_binary"]
        X = sm.add_constant(df_clean[ind_vars].select_dtypes(include=[np.number]))
        
        try:
            model = sm.Logit(y, X).fit(disp=False)
        except Exception as e:
            raise ValueError(f"Logistic regression model failed to converge: {str(e)}")

        # Coefficients and Odds Ratios table
        coefficients = []
        conf_int = model.conf_int(alpha=0.05)
        for col_name in X.columns:
            coef_val = float(model.params[col_name])
            std_err = float(model.bse[col_name])
            z_val = float(model.tvalues[col_name])
            p_val = float(model.pvalues[col_name])
            
            ci_low_log, ci_high_log = conf_int.loc[col_name]
            
            odds_ratio = float(np.exp(coef_val))
            or_ci_low = float(np.exp(ci_low_log))
            or_ci_high = float(np.exp(ci_high_log))
            
            coefficients.append({
                "variable": str(col_name),
                "log_odds_coef": coef_val,
                "std_error": std_err,
                "z_statistic": z_val,
                "p_value": p_val,
                "odds_ratio": odds_ratio,
                "or_ci_95_lower": or_ci_low,
                "or_ci_95_upper": or_ci_high,
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

        mcfadden_r2 = float(1.0 - (model.llf / model.llnull)) if model.llnull != 0 else 0.0
        mcfadden_r2 = max(0.0, min(1.0, mcfadden_r2))

        main_results = {
            "test_type": "Maximum Likelihood Binary Logistic Regression (Logit Link)",
            "outcome_mapping": {str(unique_vals[0]): 0, str(unique_vals[1]): 1},
            "mcfadden_pseudo_r_squared": mcfadden_r2,
            "log_likelihood_full": float(model.llf),
            "log_likelihood_null": float(model.llnull),
            "likelihood_ratio_chi2": float(model.llr),
            "likelihood_ratio_p_value": float(model.llr_pvalue),
            "dof_model": float(model.df_model),
            "aic": float(model.aic),
            "bic": float(model.bic),
            "coefficients": coefficients,
            "vif_diagnostics": vif_dict
        }

        effect_sizes = {
            "mcfadden_pseudo_r2": mcfadden_r2,
            "interpretation": "Poor Fit" if mcfadden_r2 < 0.1 else ("Acceptable/Good Fit" if mcfadden_r2 < 0.4 else "Excellent Fit")
        }

        # Code Generation
        r_context = {
            "dep_var": dep_var,
            "ind_vars": ind_vars,
            "conf_level": options.get("conf_level", 0.95)
        }
        r_code = self.generate_r_code(variables, r_context)
        py_code = self._generate_python_code(dep_var, ind_vars)

        # Plots
        fitted_probs = pd.Series(model.predict(X))
        plots = self.generate_plots(df_clean, variables, {"fitted_probs": fitted_probs, "actual_y": df_clean[dep_var]})

        # Interpretation
        interpretation = self.interpret({"main": main_results, "effect": effect_sizes}, variables)

        warnings = []
        if any(v > 10.0 for v in vif_dict.values()):
            warnings.append("Severe multicollinearity (VIF > 10) detected among one or more predictors. Odds Ratio estimates may be unstable.")

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
                "Hosmer Jr, D. W., Lemeshow, S., & Sturdivant, R. X. (2013). Applied Logistic Regression (3rd ed.). John Wiley & Sons.",
                "McFadden, D. (1974). Conditional logit analysis of qualitative choice behavior. Frontiers in Econometrics, 105-142."
            ]
        )

    def generate_r_code(self, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> str:
        options = options or {}
        return CodeGenerator.render_r_template("logistic_regression.R.j2", options)

    def _generate_python_code(self, dep_var: str, ind_vars: List[str]) -> str:
        preds_str = "', '".join(ind_vars)
        code = f"""import pandas as pd
import statsmodels.api as sm
import numpy as np

# Prepare clean data
predictors = ['{preds_str}']
clean_df = data[['{dep_var}'] + predictors].dropna()

# Map binary outcome to 0 and 1
vals = sorted(clean_df['{dep_var}'].unique())
mapping = {{vals[0]: 0, vals[1]: 1}}
y = clean_df['{dep_var}'].map(mapping)
X = sm.add_constant(clean_df[predictors])

# Fit Binary Logistic Regression Model (Logit)
model = sm.Logit(y, X).fit()
print(model.summary())

# Exponentiate coefficients to obtain Odds Ratios
odds_ratios = np.exp(model.params)
conf_int = np.exp(model.conf_int())
conf_int['OR'] = odds_ratios
conf_int.columns = ['CI_Lower', 'CI_Upper', 'Odds_Ratio']
print("\\nOdds Ratios (exp(beta)):")
print(conf_int[['Odds_Ratio', 'CI_Lower', 'CI_Upper']])
"""
        return CodeGenerator.format_python_code(self.method_name, code)

    def generate_plots(self, data: pd.DataFrame, variables: Dict[str, Any], results: Dict[str, Any]) -> List[Dict[str, Any]]:
        fitted_probs = results["fitted_probs"]
        actual_y = results["actual_y"]
        dep_var = variables["dependent"]

        p1 = plotter.plot_logistic_probabilities(
            fitted_probs=fitted_probs,
            actual_y=actual_y,
            title=f"Binary Logistic Regression: Predicted Event Probabilities by {dep_var}",
            subtitle="Boxplot of model predicted P(Outcome = 1) across the actual observed classes"
        )
        plots = [p1]

        # ROC Curve
        try:
            p2 = plotter.plot_roc_curve(
                actual_y=pd.Series(actual_y),
                fitted_probs=pd.Series(fitted_probs),
                title=f"ROC Curve & Classification Discriminative Power ({dep_var})"
            )
            plots.append(p2)
        except Exception:
            pass

        # Forest plot of Odds Ratios
        try:
            coefs = results.get("main", {}).get("coefficients", [])
            if coefs:
                rows = []
                idx = []
                for c in coefs:
                    if c["variable"].lower() != "intercept":
                        idx.append(c["variable"])
                        rows.append({
                            "Odds_Ratio": c["odds_ratio"],
                            "CI_Lower": c["or_ci_95_lower"],
                            "CI_Upper": c["or_ci_95_upper"]
                        })
                if rows:
                    conf_df = pd.DataFrame(rows, index=idx)
                    p3 = plotter.plot_forest_odds_ratios(
                        conf_int_df=conf_df,
                        title=f"Forest Plot of Odds Ratios (95% CI) for {dep_var}"
                    )
                    plots.append(p3)
        except Exception:
            pass

        return plots

    def interpret(self, results: Dict[str, Any], variables: Dict[str, Any]) -> str:
        main = results["main"]
        effect = results["effect"]
        dep = variables["dependent"]

        p_val = main["likelihood_ratio_p_value"]
        sig_str = "statistically significant" if p_val < 0.05 else "not statistically significant"
        p_display = f"p < 0.001" if p_val < 0.001 else f"p = {p_val:.3f}"

        lines = [
            f"A **{main['test_type']}** was fitted to predict likelihood of **{dep}** (0 vs 1) using **{main['dof_model']:.0f}** predictors ($n={results.get('sample_size', 'N')}$).",
            f"\n**Model Summary:**",
            f"- The overall model chi-square likelihood ratio test was {sig_str} ($\\chi^2({main['dof_model']:.0f}) = {main['likelihood_ratio_chi2']:.2f}, {p_display}$).",
            f"- McFadden's pseudo-$R^2$ is **{effect['mcfadden_pseudo_r2']:.3f}** ({effect['interpretation']}).",
            f"\n**Odds Ratios & Significant Predictors:**"
        ]

        sig_coefs = [c for c in main["coefficients"] if c["variable"] != "const" and c["significant"]]
        if sig_coefs:
            for sc in sig_coefs:
                or_str = f"an increase" if sc["odds_ratio"] > 1.0 else "a decrease"
                lines.append(f"- **{sc['variable']}**: Odds Ratio ($OR$) = **{sc['odds_ratio']:.2f}** (95% CI [{sc['or_ci_95_lower']:.2f}, {sc['or_ci_95_upper']:.2f}], $p = {sc['p_value']:.3f}$), indicating that each unit increase in {sc['variable']} is associated with {or_str} in odds of the outcome.")
        else:
            lines.append("- None of the individual predictors reached statistical significance ($\alpha = 0.05$) in predicting the binary outcome.")

        return "\n".join(lines)
