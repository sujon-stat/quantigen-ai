import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from typing import Any, Dict, List, Optional
from backend.app.models.analysis import MethodResult
from backend.app.models.assumptions import AssumptionResult, AssumptionRule, CheckResult
from backend.app.core.exceptions import StatisticalViolationException
from backend.app.services.statistics.base import BaseStatisticalMethod
from backend.app.services.r_integration.code_gen import CodeGenerator
from backend.app.services.visualization import plotter


class ANCOVAMethod(BaseStatisticalMethod):
    """
    Analysis of Covariance (ANCOVA).
    Compares categorical group means of a continuous outcome variable while statistically adjusting/controlling
    for one or more continuous covariates.
    """
    method_id = "ancova"
    method_name = "Analysis of Covariance (ANCOVA)"
    method_family = "ANOVA & Multi-Group Comparisons"
    description = "Tests whether group means of a continuous dependent variable differ across categorical levels after controlling for continuous covariate(s)."
    
    required_variables = {
        "dependent": ["continuous"],
        "grouping": ["categorical"],
        "covariates": ["continuous"]
    }
    optional_variables = {}

    def run(self, data: pd.DataFrame, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> MethodResult:
        options = options or {}
        
        dep_var = variables.get("dependent")
        if isinstance(dep_var, list): dep_var = dep_var[0] if dep_var else None
        
        grp_var = variables.get("grouping")
        if isinstance(grp_var, list): grp_var = grp_var[0] if grp_var else None
        
        cov_vars = variables.get("covariates", [])
        if isinstance(cov_vars, str): cov_vars = [cov_vars] if cov_vars else []
        elif not isinstance(cov_vars, list): cov_vars = []
        
        # Also check options or fallback if empty
        if not cov_vars and options.get("covariates"):
            cov_opts = options.get("covariates")
            cov_vars = [cov_opts] if isinstance(cov_opts, str) else list(cov_opts)

        if not dep_var or not grp_var:
            raise StatisticalViolationException("ANCOVA requires both a dependent variable and a grouping factor.")
        if not cov_vars:
            raise StatisticalViolationException("ANCOVA requires at least one continuous covariate to adjust for.")

        # Clean dataset across all required columns
        all_cols = [dep_var, grp_var] + cov_vars
        missing_cols = [c for c in all_cols if c not in data.columns]
        if missing_cols:
            raise StatisticalViolationException(f"Columns not found in dataset: {missing_cols}")

        clean_data = data[all_cols].dropna().copy()
        N = len(clean_data)
        if N < len(cov_vars) + 4:
            raise StatisticalViolationException(f"Insufficient sample size ({N}) for ANCOVA with {len(cov_vars)} covariate(s).")

        clean_data[dep_var] = pd.to_numeric(clean_data[dep_var], errors="coerce")
        for cv in cov_vars:
            clean_data[cv] = pd.to_numeric(clean_data[cv], errors="coerce")
        clean_data = clean_data.dropna()
        N = len(clean_data)

        # Convert grouping variable to categorical strings
        clean_data["_grp_str_"] = clean_data[grp_var].astype(str)
        groups = clean_data["_grp_str_"].unique()
        k_groups = len(groups)
        if k_groups < 2:
            raise StatisticalViolationException(f"Grouping variable '{grp_var}' must have at least 2 distinct categories (found {k_groups}).")

        # 1. Homogeneity of Regression Slopes Assumption Check
        # Test if covariate * group interaction is significant
        warnings = []
        assumptions = []
        interaction_p_vals = {}
        for cv in cov_vars:
            try:
                # Rename columns temporarily for formula safety
                clean_data["_dep_"] = clean_data[dep_var]
                clean_data["_cov_"] = clean_data[cv]
                int_model = ols("_dep_ ~ _cov_ * C(_grp_str_)", data=clean_data).fit()
                int_table = sm.stats.anova_lm(int_model, typ=2)
                int_row_key = [r for r in int_table.index if ":" in str(r) or "*" in str(r)]
                if int_row_key:
                    p_int = float(int_table.loc[int_row_key[0], "PR(>F)"])
                    interaction_p_vals[cv] = p_int
                    if p_int < 0.05:
                        warnings.append(f"Assumption Violation: Homogeneity of Regression Slopes failed for covariate '{cv}' (interaction p = {p_int:.4f}). Slopes differ across groups.")
            except Exception as e:
                pass

        # Create formal assumption check result
        min_p_int = min(interaction_p_vals.values()) if interaction_p_vals else 1.0
        assumptions.append(
            AssumptionResult(
                assumption_name="Homogeneity of Regression Slopes",
                check_result=CheckResult.VIOLATED if min_p_int < 0.05 else CheckResult.MET,
                statistic_value=min_p_int,
                p_value=min_p_int,
                details=f"Tested group × covariate interactions across {len(cov_vars)} covariate(s). Minimum interaction p-value = {min_p_int:.4f}.",
                remedy="Consider including interaction terms in a moderated regression model or stratifying analysis if slopes are heterogeneous." if min_p_int < 0.05 else None
            )
        )

        # 2. Main ANCOVA Model Execution (Type II / Type III ANOVA)
        # Build formula safe columns
        clean_data["_dep_safe_"] = clean_data[dep_var]
        safe_cov_names = []
        for idx, cv in enumerate(cov_vars):
            safe_name = f"_cov_safe_{idx}_"
            clean_data[safe_name] = clean_data[cv]
            safe_cov_names.append(safe_name)

        formula = "_dep_safe_ ~ " + " + ".join(safe_cov_names) + " + C(_grp_str_)"
        ancova_model = ols(formula, data=clean_data).fit()
        anova_table = sm.stats.anova_lm(ancova_model, typ=2)

        # Extract Group Main Effect
        grp_row = [r for r in anova_table.index if "C(_grp_str_)" in str(r)][0]
        f_group = float(anova_table.loc[grp_row, "F"])
        p_group = float(anova_table.loc[grp_row, "PR(>F)"])
        df_group = int(anova_table.loc[grp_row, "df"])
        ss_group = float(anova_table.loc[grp_row, "sum_sq"])

        # Extract Residuals
        resid_row = [r for r in anova_table.index if "Residual" in str(r)][0]
        df_error = int(anova_table.loc[resid_row, "df"])
        ss_error = float(anova_table.loc[resid_row, "sum_sq"])
        mse_error = ss_error / max(df_error, 1)

        # Calculate Partial Eta-Squared for Grouping Factor
        eta_sq_group = ss_group / (ss_group + ss_error) if (ss_group + ss_error) > 0 else 0.0

        # Extract Covariate Effects
        covariate_results = []
        for idx, cv in enumerate(cov_vars):
            safe_name = safe_cov_names[idx]
            if safe_name in anova_table.index:
                f_cov = float(anova_table.loc[safe_name, "F"])
                p_cov = float(anova_table.loc[safe_name, "PR(>F)"])
                df_cov = int(anova_table.loc[safe_name, "df"])
                ss_cov = float(anova_table.loc[safe_name, "sum_sq"])
                eta_sq_cov = ss_cov / (ss_cov + ss_error) if (ss_cov + ss_error) > 0 else 0.0
                
                # Get regression coefficient from model params
                beta_cov = float(ancova_model.params.get(safe_name, 0.0))
                se_cov = float(ancova_model.bse.get(safe_name, 0.0))
                t_cov = float(ancova_model.tvalues.get(safe_name, 0.0))
                
                covariate_results.append({
                    "covariate": cv,
                    "f_statistic": f_cov,
                    "p_value": p_cov,
                    "df": df_cov,
                    "sum_sq": ss_cov,
                    "partial_eta_squared": eta_sq_cov,
                    "coefficient": beta_cov,
                    "std_error": se_cov,
                    "t_statistic": t_cov
                })

        # 3. Calculate Unadjusted (Raw) vs Adjusted (Estimated Marginal) Means
        # Adjusted mean evaluated at the sample grand mean of all covariates
        cov_grand_means = {safe_cov_names[idx]: clean_data[safe_cov_names[idx]].mean() for idx in range(len(cov_vars))}
        group_summaries = []
        for g_val in sorted(groups):
            sub = clean_data[clean_data["_grp_str_"] == g_val]
            n_grp = len(sub)
            raw_mean = float(sub[dep_var].mean())
            raw_sd = float(sub[dep_var].std()) if n_grp > 1 else 0.0
            
            # Predict adjusted mean from fitted ANCOVA model
            pred_dict = {"_grp_str_": [g_val]}
            for s_cov, g_mean in cov_grand_means.items():
                pred_dict[s_cov] = [g_mean]
            pred_df = pd.DataFrame(pred_dict)
            adj_mean = float(ancova_model.predict(pred_df).iloc[0])
            
            # Standard error of adjusted mean roughly sqrt(MSE / n_grp)
            se_adj = float(np.sqrt(mse_error / max(n_grp, 1)))
            
            group_summaries.append({
                "category": str(g_val),
                "n": int(n_grp),
                "raw_mean": raw_mean,
                "raw_sd": raw_sd,
                "adjusted_mean": adj_mean,
                "adjusted_se": se_adj,
                "mean": adj_mean,  # primary mean for standard summary UI
                "std": raw_sd
            })

        # 4. Generate Python Code
        py_code = f"""# StatMind AI ANCOVA Execution
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols

# Clean dataset
clean_df = data[['{dep_var}', '{grp_var}', {', '.join([repr(c) for c in cov_vars])}]].dropna()

# Fit ANCOVA Model (Outcome ~ Covariates + Factor)
formula = "{dep_var} ~ { + ' + '.join([repr(c) for c in cov_vars]) } + C({grp_var})"
ancova_model = ols(formula, data=clean_df).fit()

# Type II ANOVA Table
anova_table = sm.stats.anova_lm(ancova_model, typ=2)
print(anova_table)
"""

        # 5. Generate R Code
        r_code = f"""# StatMind AI ANCOVA in R
library(car)

clean_data <- na.omit(dataset[, c('{dep_var}', '{grp_var}', {', '.join([repr(c) for c in cov_vars])})])
clean_data${grp_var} <- as.factor(clean_data${grp_var})

# Fit Linear Model
ancova_model <- lm({dep_var} ~ {' + '.join(cov_vars)} + {grp_var}, data = clean_data)

# Type II Anova Table
Anova(ancova_model, type = "II")
"""

        # 6. Generate Plotly Figure (Adjusted vs Raw Group Means Comparison Chart)
        plots = []
        try:
            fig = plotter.plot_bar_chart(
                categories=[gs["category"] for gs in group_summaries],
                values=[gs["adjusted_mean"] for gs in group_summaries],
                error_bars=[gs["adjusted_se"] * 1.96 for gs in group_summaries],
                title=f"Adjusted vs. Raw Means of {dep_var} across {grp_var} (controlling for {', '.join(cov_vars)})",
                x_label=grp_var,
                y_label=f"Adjusted Mean ({dep_var})"
            )
            if fig: plots.append(fig)
        except Exception:
            pass

        # 7. Interpretation text
        sig_str = "statistically significant" if p_group < 0.05 else "not statistically significant"
        interpretation = (
            f"An Analysis of Covariance (ANCOVA) was conducted to compare the effect of '{grp_var}' on '{dep_var}' while adjusting for "
            f"covariate(s): {', '.join(cov_vars)}. After controlling for the covariate(s), there was a {sig_str} main effect of group "
            f"on '{dep_var}', F({df_group}, {df_error}) = {f_group:.4f}, p = {p_group:.4f}, partial η² = {eta_sq_group:.4f}. "
            f"Estimated marginal (adjusted) means were evaluated at the covariate grand means."
        )

        return MethodResult(
            method_id=self.method_id,
            method_name=self.method_name,
            method_family=self.method_family,
            description=self.description,
            variables_used=variables,
            sample_size=N,
            assumption_results=assumptions,
            main_results={
                "f_statistic": f_group,
                "p_value": p_group,
                "degrees_of_freedom_between": df_group,
                "degrees_of_freedom_within": df_error,
                "k_groups": k_groups,
                "group_summaries": group_summaries,
                "covariate_results": covariate_results,
                "anova_table_summary": {
                    "f_statistic": f_group,
                    "p_value": p_group,
                    "df_between": df_group,
                    "df_within": df_error,
                    "ss_between": ss_group,
                    "ss_within": ss_error
                }
            },
            effect_sizes={
                "partial_eta_squared": eta_sq_group,
                "eta_squared": eta_sq_group
            },
            post_hoc_results=None,
            python_code=py_code,
            r_code=r_code,
            plots=plots,
            interpretation=interpretation,
            warnings=warnings,
            references=[
                "Field, A. (2018). Discovering statistics using IBM SPSS statistics (5th ed.). SAGE Publications.",
                "Maxwell, S. E., Delaney, H. D., & Kelley, K. (2017). Designing experiments and analyzing data: A model comparison perspective. Routledge."
            ]
        )
