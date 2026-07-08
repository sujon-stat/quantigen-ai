import time
import pandas as pd
from typing import Any, Dict, Optional
from backend.app.models.analysis import MethodResult
from backend.app.core.exceptions import AnalysisFailedException, StatisticalViolationException, ResourceExceededException
from backend.app.services.statistics.registry import MethodRegistry
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
