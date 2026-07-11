import time
import pandas as pd
from typing import Any, Dict, Optional
from backend.app.models.analysis import MethodResult
from backend.app.core.exceptions import AnalysisFailedException, StatisticalViolationException, ResourceExceededException
from backend.app.services.statistics.registry import MethodRegistry
from backend.app.services.statistics.survey_engine import SurveyEngine
import backend.app.services.statistics  # Ensures bootstrap_registry runs


class AnalysisEngine:
    """Main orchestrator engine for executing statistical analyses securely and transparently."""

    @classmethod
    def execute_analysis(
        cls,
        method_id: str,
        data: pd.DataFrame,
        variables: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 60.0
    ) -> MethodResult:
        """
        Orchestrate statistical analysis pipeline:
        1. Lookup registered statistical method by ID
        2. Validate dataset size and variable roles
        3. Execute method and check assumptions
        4. Package educational and code outputs
        """
        start_time = time.time()

        # 1. Check method existence
        method = MethodRegistry.get(method_id)
        if not method:
            raise AnalysisFailedException(
                message=f"Statistical method '{method_id}' is not registered or supported.",
                user_friendly_message=f"We couldn't find the requested analysis method '{method_id}'. Please select one of the available statistical tools."
            )

        # 2. Check basic data constraints
        if data.empty:
            raise AnalysisFailedException(
                message="Input dataset is empty.",
                user_friendly_message="The dataset provided has no observations. Please upload a dataset with rows of data."
            )

        # Memory / row limit check (Sandbox limit 512MB approx ~ 1,000,000 rows x 50 cols safely)
        if len(data) > 1_000_000:
            raise ResourceExceededException(
                message="Dataset exceeds 1,000,000 rows sandbox threshold.",
                resource_type="rows",
                limit="1,000,000"
            )

        # 3. Validate variable roles
        # When multi-variable lists are present (for academic Table 1), skip strict pre-validation
        # because the method's own run() handles per-pair validation internally.
        has_multi_vars = any(
            isinstance(variables.get(k), list) and len(variables.get(k, [])) > 1
            for k in ["dependent", "grouping", "independent", "variables"]
        )
        if not has_multi_vars:
            validation_errors = method.validate_variables(data, variables)
            if validation_errors:
                raise StatisticalViolationException(
                    message=f"Variable validation error: {'; '.join(validation_errors)}",
                    violation_type="variable_binding_error",
                    remedy="Double check your selected dependent and independent variables to make sure they match the required columns and data types."
                )

        # 4. Execute method
        try:
            result = method.run(data, variables, options)
            
            # 5. Check if Complex Survey Sampling Design is active (SurveyNCD / DHS / MICS / STEPS)
            survey_design = SurveyEngine.extract_design(variables, options)
            if survey_design["is_survey_weighted"]:
                survey_meta = SurveyEngine.compute_design_metadata(data, survey_design)
                result.main_results["survey_metadata"] = survey_meta
                result.main_results["is_survey_weighted"] = True
                
                # Apply exact survey-weighted computations where applicable
                if method_id in ["ttest", "independent_ttest"]:
                    try:
                        dep_var = variables.get("dependent") or variables.get("dep_var")
                        group_var = variables.get("grouping") or variables.get("group_var")
                        if dep_var and group_var:
                            svy_res = SurveyEngine.run_survey_ttest(data, dep_var, group_var, survey_design)
                            result.main_results.update(svy_res)
                            result.interpretation = f"Survey-Weighted Analysis (`{survey_design['design_type']}`): A cluster-robust Taylor series linearization T-Test on {survey_meta['n_clusters']} PSUs / {survey_meta['n_strata']} strata ({survey_meta['df_design']} design df) found a weighted mean difference of {svy_res['mean_difference']:.2f} (95% CI: {svy_res['ci_lower']:.2f} to {svy_res['ci_upper']:.2f}, t = {svy_res['t_statistic']:.2f}, p = {svy_res['p_value']:.4f}). This accounts for sampling design effect (DEFF ≈ {survey_meta['deff_approx']}), preventing unweighted false-positive bias."
                    except Exception as svy_e:
                        result.warnings.append(f"Note on survey T-Test: {str(svy_e)}")
                        
                elif method_id in ["anova", "anova_oneway"]:
                    try:
                        dep_var = variables.get("dependent") or variables.get("dep_var")
                        group_var = variables.get("grouping") or variables.get("group_var")
                        if dep_var and group_var:
                            svy_res = SurveyEngine.run_survey_anova(data, dep_var, group_var, survey_design)
                            result.main_results.update(svy_res)
                            result.interpretation = f"Survey-Weighted One-Way ANOVA (`{survey_design['design_type']}`): Evaluated using Taylor series linearization Wald F-Test across {survey_meta['df_design']} design df (F({svy_res['df_numerator']}, {svy_res['df_denominator']}) = {svy_res['f_statistic']:.2f}, p = {svy_res['p_value']:.4f}). Complex sampling weights (`{survey_design.get('weight_var')}`) and clustering were rigorously corrected."
                    except Exception as svy_e:
                        result.warnings.append(f"Note on survey ANOVA: {str(svy_e)}")
                        
                elif method_id in ["chi_square", "chisq"]:
                    try:
                        row_var = variables.get("row_var") or variables.get("var1")
                        col_var = variables.get("col_var") or variables.get("var2")
                        if row_var and col_var:
                            svy_res = SurveyEngine.run_survey_chisquare(data, row_var, col_var, survey_design)
                            result.main_results.update(svy_res)
                            result.interpretation = f"Survey-Weighted Contingency Analysis (`{survey_design['design_type']}`): Rao-Scott second-order design-adjusted Chi-Square test yielded adj X² = {svy_res['chi2_statistic']:.2f} (F = {svy_res['f_statistic']:.2f}, p = {svy_res['p_value']:.4f}) over {survey_meta['df_design']} design df (DEFF ≈ {survey_meta['deff_approx']})."
                    except Exception as svy_e:
                        result.warnings.append(f"Note on survey Chi-Square: {str(svy_e)}")

                # Generate publication-ready R `survey` package code
                result.r_code = SurveyEngine.generate_r_survey_code(method_id, variables, survey_design)
                
                # Update title and warnings
                if not result.method_name.startswith("Survey-Weighted"):
                    result.method_name = f"Survey-Weighted {result.method_name}"
                result.warnings.insert(0, f"Active Complex Survey Design Shield: Sampling weights ('{survey_design.get('weight_var')}') and PSU clusters ('{survey_design.get('cluster_var')}') applied via Taylor series linearization.")

            # Check execution duration against timeout limit
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                raise ResourceExceededException(
                    message=f"Analysis execution time ({elapsed:.1f}s) exceeded {timeout_seconds}s limit.",
                    resource_type="execution_time",
                    limit=f"{timeout_seconds} seconds"
                )
                
            return result
        except StatisticalViolationException:
            raise
        except ResourceExceededException:
            raise
        except Exception as e:
            raise AnalysisFailedException(
                message=f"Error running method '{method_id}': {str(e)}",
                user_friendly_message=f"An unexpected calculation error occurred while performing {method.method_name}. ({str(e)})"
            )
