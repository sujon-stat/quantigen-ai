import time
import pandas as pd
from typing import Any, Dict, List, Optional
from backend.app.models.analysis import MethodResult, AssumptionResult
from backend.app.core.exceptions import AnalysisFailedException, StatisticalViolationException, ResourceExceededException
from backend.app.services.statistics.registry import MethodRegistry
from backend.app.services.statistics.survey_engine import SurveyEngine
from backend.app.services.statistics.batch_engine import run_batch
from backend.app.services.statistics.power_engine import PowerAnalysisEngine
import backend.app.services.statistics  # Ensures bootstrap_registry runs


# Methods that support the centralized Batch Execution engine
GROUP_COMPARISON_METHODS = {
    "ttest_independent",
    "anova_oneway",
    "mann_whitney_u",
    "kruskal_wallis",
    "ancova",
}


def _batch_to_method_result(batch: Dict[str, Any], method_id: str, variables: Dict[str, Any]) -> MethodResult:
    """Convert a batch_engine output dict into a MethodResult the frontend understands."""
    rows = batch["rows"]
    corrections = batch["auto_corrections"]
    n = batch["n_comparisons"]

    method_name_map = {
        "ttest_independent": "Independent Samples T-Test",
        "anova_oneway": "One-Way ANOVA",
        "mann_whitney_u": "Mann-Whitney U Test",
        "kruskal_wallis": "Kruskal-Wallis H Test",
        "ancova": "Analysis of Covariance (ANCOVA)",
    }
    base_name = method_name_map.get(method_id, method_id)

    # Collect all group-level descriptives for the results component
    all_summaries = []
    for row in rows:
        if row.get("status") == "success" and row.get("group_summaries"):
            for gs in row["group_summaries"]:
                all_summaries.append({
                    **gs,
                    "variable": row["dependent_var"],
                    "grouping_column": row["grouping_var"],
                })

    total_n = max((r.get("n_total", 0) for r in rows if r.get("status") == "success"), default=0)

    warnings: List[str] = list(corrections)
    errors = [r["error_message"] for r in rows if r.get("status") == "error" and r.get("error_message")]
    if errors:
        warnings.extend(errors)

    return MethodResult(
        method_id=method_id,
        method_name=f"Batch {base_name} — Academic Table 1" if n > 1 else base_name,
        method_family="Group Comparisons",
        description=(
            f"Batch execution across {n} comparison(s). "
            + (f"{len(corrections)} auto-correction(s) applied by Agentic Shield." if corrections else "")
        ),
        variables_used=variables,
        sample_size=total_n,
        assumption_results=[],
        main_results={
            "test_type": f"Batch {base_name}",
            "multi_variable_table": rows,
            "group_summaries": all_summaries,
            "auto_corrections": corrections,
            "is_batch": batch["is_batch"],
            "n_comparisons": n,
        },
        effect_sizes={"summary": f"Effect sizes computed per comparison (see table)."},
        python_code=f"# Batch execution — see individual comparison results",
        r_code=f"# Batch execution — see individual comparison results",
        plots=[],
        interpretation=(
            f"Batch statistical comparison table generated across {n} variable pair(s). "
            + (f"⚡ Agentic Shield applied {len(corrections)} auto-correction(s): " + "; ".join(corrections) if corrections else "")
        ),
        warnings=warnings,
    )


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

        # 3. Batch Execution Engine (for group comparison methods with multiple variables)
        # This is the "Table 1 Generation" / Batch feature.
        # Detect if caller passed lists for dep/grouping variables
        raw_dep = variables.get("dependent") or variables.get("var1")
        raw_grp = variables.get("grouping") or variables.get("independent")
        dep_list = raw_dep if isinstance(raw_dep, list) else ([raw_dep] if raw_dep else [])
        grp_list = raw_grp if isinstance(raw_grp, list) else ([raw_grp] if raw_grp else [])
        dep_list = [d for d in dep_list if d]  # remove None/empty
        grp_list = [g for g in grp_list if g]

        is_batch_call = method_id in GROUP_COMPARISON_METHODS and (len(dep_list) > 1 or len(grp_list) > 1)

        if is_batch_call:
            batch = run_batch(
                data=data,
                dep_vars=dep_list,
                grp_vars=grp_list,
                requested_method=method_id,
                options=options,
            )
            return _batch_to_method_result(batch, method_id, variables)

        # Single-variable path: validate normally
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

            # Attach exact post-hoc statistical power and sensitivity analysis
            PowerAnalysisEngine.attach_post_hoc_power(result)

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
