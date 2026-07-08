import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional
from backend.app.models.assumptions import AssumptionRule, AssumptionResult, Severity
from backend.app.models.variables import VariableType
from backend.app.services.assumptions.rules import get_rules_for_method
from backend.app.services.assumptions import tests
from backend.app.services.assumptions.explanations import generate_explanation


class AssumptionChecker:
    """Central engine for executing assumption checks before running statistical methods."""

    @classmethod
    def _get_clean_analysis_data(cls, data: pd.DataFrame, variables: Dict[str, Any]) -> pd.DataFrame:
        cols = set()
        for k, v in variables.items():
            if isinstance(v, str) and v in data.columns:
                cols.add(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, str) and item in data.columns:
                        cols.add(item)
        if not cols:
            return data
        return data[list(cols)].dropna()

    @classmethod
    def check_all(cls, method_id: str, data: pd.DataFrame, variables: Dict[str, Any]) -> List[AssumptionResult]:
        """Run all assumption checks registered for a statistical method against input data."""
        rules = get_rules_for_method(method_id)
        results = []
        
        # Calculate minimum / total effective sample size on used variables only
        clean_df = cls._get_clean_analysis_data(data, variables)
        n_total = len(clean_df)
        
        for rule in rules:
            result = cls._run_single_test(rule, data, variables)
            # Adjust severity based on sample size (e.g. CLT rule)
            result = cls.adjust_severity_by_sample_size(result, n_total, variables, data)
            results.append(result)
            
        return results

    @classmethod
    def _run_single_test(cls, rule: AssumptionRule, data: pd.DataFrame, variables: Dict[str, Any]) -> AssumptionResult:
        test_name = rule.test_name
        passed = True
        test_stat = None
        p_val = None
        details = {}
        
        # 1. Sample size checks
        if test_name == "sample_size_check" or test_name == "regression_sample_size":
            clean_df = cls._get_clean_analysis_data(data, variables)
            n = len(clean_df)
            test_stat = float(n)
            threshold = rule.threshold or 5.0
            if test_name == "regression_sample_size":
                # For regression, n >= 10 * p
                independent_vars = variables.get("independent", [])
                if isinstance(independent_vars, str):
                    p_count = 1
                else:
                    p_count = len(independent_vars) if independent_vars else 1
                threshold = max(10.0, 10.0 * p_count)
            passed = bool(n >= threshold)
            details = {"sample_size": n, "required_threshold": threshold}

        elif test_name == "group_sample_size_check":
            dep_var = variables.get("dependent")
            group_var = variables.get("grouping")
            if dep_var and group_var and dep_var in data.columns and group_var in data.columns:
                group_sizes = data[[dep_var, group_var]].dropna().groupby(group_var).size()
                min_n = int(group_sizes.min()) if not group_sizes.empty else 0
                test_stat = float(min_n)
                passed = bool(min_n >= (rule.threshold or 5.0))
                details = {"min_group_size": min_n, "group_counts": group_sizes.to_dict()}
            else:
                passed = False
                details = {"error": "Missing dependent or grouping variable columns"}

        # 2. Variable type check
        elif test_name == "variable_type_check":
            # Type checking is handled upstream during data/variable validation
            passed = True
            details = {"status": "Checked during variable binding"}

        # 3. Design check
        elif test_name == "design_check":
            # User design checks default to met or validated via UI confirmation
            passed = True
            details = {"status": "Design verified by user selection"}

        # 4. Shapiro-Wilk normality
        elif test_name == "shapiro_wilk":
            dep_var = variables.get("dependent")
            group_var = variables.get("grouping")
            if dep_var and dep_var in data.columns:
                if group_var and group_var in data.columns:
                    # Test normality inside each group
                    groups = data[[dep_var, group_var]].dropna()[group_var].unique()
                    all_passed = True
                    min_p = 1.0
                    stat_sum = 0.0
                    for g in groups:
                        g_series = data[data[group_var] == g][dep_var]
                        g_pass, g_stat, g_p, _ = tests.test_shapiro_wilk(g_series)
                        if not g_pass:
                            all_passed = False
                        min_p = min(min_p, g_p)
                        stat_sum += g_stat
                    passed = all_passed
                    test_stat = stat_sum / len(groups) if len(groups) > 0 else 0.0
                    p_val = min_p
                else:
                    passed, test_stat, p_val, details = tests.test_shapiro_wilk(data[dep_var])
            else:
                passed, details = False, {"error": f"Variable '{dep_var}' not found"}

        elif test_name == "shapiro_wilk_bivariate":
            vars_list = variables.get("variables", [])
            if len(vars_list) >= 2 and all(v in data.columns for v in vars_list[:2]):
                p1, s1, pv1, _ = tests.test_shapiro_wilk(data[vars_list[0]])
                p2, s2, pv2, _ = tests.test_shapiro_wilk(data[vars_list[1]])
                passed = p1 and p2
                test_stat = (s1 + s2) / 2.0
                p_val = min(pv1, pv2)
            else:
                passed = False

        elif test_name in ["shapiro_wilk_residuals", "shapiro_wilk_multiple_residuals"]:
            dep_var = variables.get("dependent")
            ind_vars = variables.get("independent")
            if isinstance(ind_vars, str):
                ind_vars = [ind_vars]
            elif not isinstance(ind_vars, list):
                ind_vars = []
            if dep_var in data.columns and ind_vars and all(v in data.columns for v in ind_vars):
                passed, test_stat, p_val, details = tests.test_residuals_normality(data[dep_var], data[ind_vars])
            else:
                passed = False

        # 5. Levene's test
        elif test_name == "levene":
            dep_var = variables.get("dependent")
            group_var = variables.get("grouping")
            if dep_var in data.columns and group_var in data.columns:
                groups = [data[data[group_var] == g][dep_var] for g in data[group_var].dropna().unique()]
                passed, test_stat, p_val, details = tests.test_levene_homogeneity(groups)
            else:
                passed = False

        # 6. IQR outliers
        elif test_name == "iqr_outliers":
            dep_var = variables.get("dependent")
            if dep_var and dep_var in data.columns:
                passed, test_stat, _, details = tests.test_iqr_outliers(data[dep_var], rule.threshold or 3.0)
            else:
                passed = False

        elif test_name == "iqr_outliers_both":
            vars_list = variables.get("variables", [])
            if len(vars_list) >= 2 and all(v in data.columns for v in vars_list[:2]):
                p1, c1, _, _ = tests.test_iqr_outliers(data[vars_list[0]], rule.threshold or 3.0)
                p2, c2, _, _ = tests.test_iqr_outliers(data[vars_list[1]], rule.threshold or 3.0)
                passed = p1 and p2
                test_stat = c1 + c2
            else:
                passed = False

        # 7. Expected cell frequencies
        elif test_name == "expected_cell_frequencies":
            vars_list = variables.get("variables", [])
            if len(vars_list) >= 2 and all(v in data.columns for v in vars_list[:2]):
                c_table = pd.crosstab(data[vars_list[0]], data[vars_list[1]])
                passed, test_stat, p_val, details = tests.test_expected_cell_frequencies(c_table)
            else:
                passed = False

        # 8. Breusch-Pagan
        elif test_name == "breusch_pagan":
            dep_var = variables.get("dependent")
            ind_vars = variables.get("independent")
            if isinstance(ind_vars, str):
                ind_vars = [ind_vars]
            elif not isinstance(ind_vars, list):
                ind_vars = []
            if dep_var in data.columns and ind_vars and all(v in data.columns for v in ind_vars):
                passed, test_stat, p_val, details = tests.test_breusch_pagan(data[dep_var], data[ind_vars])
            else:
                passed = False

        # 9. Durbin-Watson
        elif test_name == "durbin_watson":
            dep_var = variables.get("dependent")
            ind_vars = variables.get("independent")
            if isinstance(ind_vars, str):
                ind_vars = [ind_vars]
            elif not isinstance(ind_vars, list):
                ind_vars = []
            if dep_var in data.columns and ind_vars and all(v in data.columns for v in ind_vars):
                df_clean = data[[dep_var] + ind_vars].dropna()
                if len(df_clean) > 2:
                    import statsmodels.api as sm
                    y = df_clean[dep_var]
                    X = sm.add_constant(df_clean[ind_vars].select_dtypes(include=[np.number]))
                    model = sm.OLS(y, X).fit()
                    passed, test_stat, _, details = tests.test_durbin_watson_autocorrelation(model.resid)
                else:
                    passed = False
            else:
                passed = False

        # 10. Cook's Distance
        elif test_name == "cooks_distance":
            dep_var = variables.get("dependent")
            ind_vars = variables.get("independent")
            if isinstance(ind_vars, str):
                ind_vars = [ind_vars]
            elif not isinstance(ind_vars, list):
                ind_vars = []
            if dep_var in data.columns and ind_vars and all(v in data.columns for v in ind_vars):
                passed, test_stat, p_val, details = tests.test_cooks_distance(data[dep_var], data[ind_vars])
            else:
                passed = False

        # 11. VIF Multicollinearity
        elif test_name == "vif_check":
            ind_vars = variables.get("independent")
            if isinstance(ind_vars, str) and ind_vars in data.columns:
                passed, test_stat, _, details = tests.test_vif_multicollinearity(data[[ind_vars]])
            elif isinstance(ind_vars, list) and all(v in data.columns for v in ind_vars):
                passed, test_stat, _, details = tests.test_vif_multicollinearity(data[ind_vars])
            else:
                passed = True # single or missing predictor

        # 12. Binary Outcome Check
        elif test_name == "binary_outcome_check":
            dep_var = variables.get("dependent")
            if dep_var in data.columns:
                passed, test_stat, _, details = tests.test_binary_outcome(data[dep_var])
            else:
                passed = False

        # Default fallback
        else:
            passed = True
            details = {"status": "Visual check or passed by default"}

        explanation = generate_explanation(
            rule=rule,
            passed=passed,
            test_statistic=test_stat,
            p_value=p_val,
            details=details,
            adjusted_severity=rule.severity
        )

        return AssumptionResult(
            assumption_name=rule.name,
            passed=passed,
            test_used=rule.test_name,
            test_statistic=test_stat,
            p_value=p_val,
            details=details,
            explanation=explanation,
            remedy=rule.remedy,
            auto_fix_available=(rule.severity == Severity.AUTO_FIX and not passed),
            auto_fix_description=f"Auto-fix ({rule.auto_fix_action}) applied automatically upon execution." if (rule.severity == Severity.AUTO_FIX and not passed) else None,
            severity=rule.severity
        )

    @classmethod
    def adjust_severity_by_sample_size(cls, assumption_result: AssumptionResult, n: int, variables: Dict[str, Any], data: pd.DataFrame) -> AssumptionResult:
        """
        Adjust assumption severity and explanation based on sample size using CLT rules.
        """
        if not assumption_result.passed and assumption_result.assumption_name == "normality":
            # Check group sample size or overall sample size
            dep_var = variables.get("dependent")
            group_var = variables.get("grouping")
            if dep_var and group_var and group_var in data.columns:
                group_sizes = data[[dep_var, group_var]].dropna().groupby(group_var).size()
                min_n = int(group_sizes.min()) if not group_sizes.empty else n
            else:
                min_n = n

            # If min group sample size > 30, CLT makes t-test robust
            if min_n > 30:
                if assumption_result.severity == Severity.ERROR:
                    assumption_result.severity = Severity.WARNING
                assumption_result.details["clt_applied"] = True
                assumption_result.details["sample_size"] = min_n
                # Regenerate explanation
                rule_mock = AssumptionRule(
                    name=assumption_result.assumption_name,
                    description=assumption_result.assumption_name.replace("_", " ").title(),
                    test_name=assumption_result.test_used,
                    severity=assumption_result.severity,
                    consequence="While non-normal distributions can distort p-values in small samples, your sample size is sufficiently large.",
                    remedy=assumption_result.remedy
                )
                assumption_result.explanation = generate_explanation(
                    rule=rule_mock,
                    passed=False,
                    test_statistic=assumption_result.test_statistic,
                    p_value=assumption_result.p_value,
                    details=assumption_result.details,
                    adjusted_severity=Severity.WARNING
                )

        return assumption_result
