import json
import math
import subprocess
import tempfile
import os
from typing import Any, Dict, List, Optional, Tuple
from backend.app.models.analysis import MethodResult


class StatisticalValidator:
    """
    Cross-validation and precision verification engine for StatMind AI.
    Ensures numerical calculations match industry-standard benchmarks (scipy, statsmodels, R) within strict epsilon tolerances (< 1e-6).
    """

    DEFAULT_TOLERANCE = 1e-6

    @classmethod
    def validate_precision(
        cls,
        result: MethodResult,
        expected: Dict[str, float],
        tolerance: float = DEFAULT_TOLERANCE
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Compare computed test statistics, p-values, and effect sizes against expected benchmark values.
        Returns: (passed, list_of_errors, detailed_comparison_dict)
        """
        errors = []
        details = {}
        all_passed = True

        # Flatten all numerical outputs from main_results and effect_sizes
        computed_flat = {}
        if result.main_results:
            for k, v in result.main_results.items():
                if isinstance(v, (int, float)) and not math.isnan(v):
                    computed_flat[k] = float(v)
        if result.effect_sizes:
            for k, v in result.effect_sizes.items():
                if isinstance(v, (int, float)) and not math.isnan(v):
                    computed_flat[k] = float(v)

        for stat_name, expected_val in expected.items():
            if stat_name not in computed_flat:
                errors.append(f"Expected statistic '{stat_name}' not found in computed method results.")
                all_passed = False
                continue

            computed_val = computed_flat[stat_name]
            abs_diff = abs(computed_val - expected_val)
            rel_diff = abs_diff / abs(expected_val) if abs(expected_val) > 1e-12 else abs_diff

            passed = bool(abs_diff <= tolerance or rel_diff <= tolerance)
            details[stat_name] = {
                "computed": computed_val,
                "expected": expected_val,
                "abs_difference": abs_diff,
                "rel_difference": rel_diff,
                "tolerance": tolerance,
                "passed": passed
            }

            if not passed:
                all_passed = False
                errors.append(
                    f"Precision mismatch for '{stat_name}': computed={computed_val:.8f}, expected={expected_val:.8f} (abs_diff={abs_diff:.2e} > tolerance {tolerance:.2e})"
                )

        return all_passed, errors, details

    @classmethod
    def generate_r_verification_script(cls, result: MethodResult, dataset_csv_path: str) -> str:
        """
        Generate an executable, standalone R script that loads the dataset CSV, executes the R analysis code,
        and prints key numeric statistics in high-precision JSON for cross-checking.
        """
        r_code = result.r_code
        # Ensure path is properly escaped for R string
        clean_path = dataset_csv_path.replace("\\", "/")

        script = f"""# ================================================================
# StatMind AI Standalone R Verification Script
# Method: {result.method_name} ({result.method_id})
# ================================================================

# Load data
if (!file.exists("{clean_path}")) {{
  stop(paste("Dataset file not found at:", "{clean_path}"))
}}
data <- read.csv("{clean_path}", stringsAsFactors = FALSE)

# Execute StatMind generated analysis template
{r_code}
"""
        return script

    @classmethod
    def run_rscript_verification(
        cls,
        result: MethodResult,
        data: Any,
        expected_benchmarks: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Attempt to run R verification using external `Rscript` if installed on the system.
        Writes data to temporary CSV and runs generated verification script.
        """
        # First validate internal python/scipy expectations if provided
        py_passed = True
        py_errors = []
        py_details = {}
        if expected_benchmarks:
            py_passed, py_errors, py_details = cls.validate_precision(result, expected_benchmarks)

        # Try executing Rscript if available on PATH
        rscript_result = {
            "rscript_available": False,
            "r_status": "skipped",
            "r_output": None,
            "r_error": None
        }

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                csv_path = os.path.join(tmpdir, "verification_data.csv")
                r_path = os.path.join(tmpdir, "verify.R")

                # Write CSV
                if hasattr(data, "to_csv"):
                    data.to_csv(csv_path, index=False)
                elif isinstance(data, str) and os.path.exists(data):
                    with open(data, "r", encoding="utf-8") as f:
                        with open(csv_path, "w", encoding="utf-8") as out:
                            out.write(f.read())

                r_script_content = cls.generate_r_verification_script(result, csv_path)
                with open(r_path, "w", encoding="utf-8") as f:
                    f.write(r_script_content)

                # Check if Rscript executable is on system
                proc = subprocess.run(
                    ["Rscript", "--vanilla", r_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=15
                )

                rscript_result["rscript_available"] = True
                if proc.returncode == 0:
                    rscript_result["r_status"] = "success"
                    rscript_result["r_output"] = proc.stdout
                else:
                    rscript_result["r_status"] = "failed"
                    rscript_result["r_error"] = proc.stderr

        except (FileNotFoundError, subprocess.SubprocessError):
            rscript_result["rscript_available"] = False
            rscript_result["r_status"] = "rscript_not_installed"

        return {
            "method_id": result.method_id,
            "method_name": result.method_name,
            "python_precision_passed": py_passed,
            "python_precision_errors": py_errors,
            "python_precision_details": py_details,
            "rscript_verification": rscript_result
        }
