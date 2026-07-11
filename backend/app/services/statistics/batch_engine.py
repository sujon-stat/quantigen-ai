"""
Quantigen AI — Batch Execution Engine
======================================
Handles the "Table 1 Generation" / Batch Execution feature.

Researchers select one or more dependent variables and one or more grouping
variables.  This engine:
  1. Standardises inputs to lists.
  2. Checks how many unique groups each grouping variable has.
  3. Auto-corrects the method per variable:
       T-Test  → ANOVA         when grouping var has > 2 groups
       Mann-Whitney → Kruskal  when grouping var has > 2 groups
  4. Executes the correct statistical test for every (dep, grp) pair.
  5. Returns a unified batch result with auto-correction notes for the UI.
"""

from __future__ import annotations

import pandas as pd
from scipy import stats
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


# ---------------------------------------------------------------------------
# Type alias for a single row in the batch results table
# ---------------------------------------------------------------------------
BatchRow = Dict[str, Any]


def _get_group_count(data: pd.DataFrame, grouping_var: str) -> int:
    """Return the number of unique non-null groups in a column."""
    if grouping_var not in data.columns:
        return 0
    return int(data[grouping_var].dropna().nunique())


def _auto_correct_method(
    requested_method: str,
    n_groups: int,
    grouping_var: str
) -> Tuple[str, Optional[str]]:
    """
    Determine the actual method to use and generate an auto-correction note.

    Returns:
        (actual_method_id, auto_correction_note_or_None)
    """
    note = None
    actual = requested_method

    if requested_method == "ttest_independent" and n_groups > 2:
        actual = "anova_oneway"
        note = (
            f"⚡ Auto-corrected: '{grouping_var}' has {n_groups} groups "
            f"(T-Test requires exactly 2). Automatically switched to One-Way ANOVA."
        )
    elif requested_method == "mann_whitney_u" and n_groups > 2:
        actual = "kruskal_wallis"
        note = (
            f"⚡ Auto-corrected: '{grouping_var}' has {n_groups} groups "
            f"(Mann-Whitney requires exactly 2). Automatically switched to Kruskal-Wallis H Test."
        )
    elif requested_method in ("anova_oneway", "kruskal_wallis") and n_groups == 2:
        # Fine to run ANOVA/Kruskal on 2 groups, no correction needed
        pass

    return actual, note


def _run_single_pair(
    data: pd.DataFrame,
    dep_var: str,
    grp_var: str,
    actual_method: str,
    options: Optional[Dict[str, Any]] = None
) -> BatchRow:
    """
    Execute the exact statistical test for a single (dep_var, grp_var) pair.
    Returns a dict containing all results for one table row.
    """
    options = options or {}

    if grp_var not in data.columns or dep_var not in data.columns:
        return {
            "dependent_var": dep_var,
            "grouping_var": grp_var,
            "method_used": actual_method,
            "status": "error",
            "error_message": f"Column '{dep_var}' or '{grp_var}' not found in dataset."
        }

    temp_df = data[[dep_var, grp_var]].dropna().copy()
    temp_df[grp_var] = temp_df[grp_var].astype(str)
    temp_df[dep_var] = pd.to_numeric(temp_df[dep_var], errors="coerce")
    temp_df = temp_df.dropna()

    groups_labels = temp_df[grp_var].unique().tolist()
    n_groups = len(groups_labels)
    group_data = [temp_df[temp_df[grp_var] == g][dep_var].values for g in groups_labels]
    n_total = int(len(temp_df))

    if n_groups < 2:
        return {
            "dependent_var": dep_var,
            "grouping_var": grp_var,
            "method_used": actual_method,
            "n_total": n_total,
            "n_groups": n_groups,
            "status": "error",
            "error_message": f"'{grp_var}' has only {n_groups} group — need at least 2 for comparison."
        }

    # --- Descriptive statistics per group ----------------------------------
    group_summaries = []
    for label, arr in zip(groups_labels, group_data):
        arr_clean = arr[~np.isnan(arr)]
        if len(arr_clean) > 0:
            group_summaries.append({
                "group": str(label),
                "n": int(len(arr_clean)),
                "mean": float(np.mean(arr_clean)),
                "sd": float(np.std(arr_clean, ddof=1)) if len(arr_clean) > 1 else 0.0,
                "median": float(np.median(arr_clean)),
                "min": float(np.min(arr_clean)),
                "max": float(np.max(arr_clean)),
            })

    # --- Statistical test --------------------------------------------------
    try:
        stat = p_val = None
        df_val = effect_size = effect_label = None

        if actual_method == "ttest_independent":
            g1, g2 = group_data[0], group_data[1]

            # Levene's test for equal variances → decide Welch vs. Student
            if len(g1) >= 2 and len(g2) >= 2:
                lev_stat, lev_p = stats.levene(g1, g2)
                equal_var = bool(lev_p > 0.05)
            else:
                equal_var = False

            stat, p_val = stats.ttest_ind(g1, g2, equal_var=equal_var)
            n1, n2 = len(g1), len(g2)

            # Welch–Satterthwaite df
            s1, s2 = float(np.std(g1, ddof=1)) if n1 > 1 else 0.0, float(np.std(g2, ddof=1)) if n2 > 1 else 0.0
            if s1 == 0 and s2 == 0:
                df_val = n1 + n2 - 2
            elif equal_var:
                df_val = n1 + n2 - 2
            else:
                num = (s1 ** 2 / n1 + s2 ** 2 / n2) ** 2
                den = (s1 ** 2 / n1) ** 2 / (n1 - 1) + (s2 ** 2 / n2) ** 2 / (n2 - 1) if n1 > 1 and n2 > 1 else 1
                df_val = num / den if den > 0 else n1 + n2 - 2

            # Cohen's d
            pooled_sd = np.sqrt((s1 ** 2 + s2 ** 2) / 2) if s1 > 0 or s2 > 0 else 1
            cohens_d = abs(float(np.mean(g1)) - float(np.mean(g2))) / pooled_sd if pooled_sd > 0 else 0.0
            effect_size = round(cohens_d, 4)
            effect_label = "Cohen's d"

            extra = {
                "test_variant": "Welch" if not equal_var else "Student",
                "levene_p": round(float(lev_p), 4) if "lev_p" in dir() else None,
                "degrees_of_freedom": round(float(df_val), 2) if df_val else None,
                "mean_group1": round(float(np.mean(g1)), 4),
                "mean_group2": round(float(np.mean(g2)), 4),
                "mean_difference": round(float(np.mean(g1)) - float(np.mean(g2)), 4),
                "group1_label": str(groups_labels[0]),
                "group2_label": str(groups_labels[1]),
            }

        elif actual_method == "anova_oneway":
            stat, p_val = stats.f_oneway(*group_data)
            df_between = n_groups - 1
            df_within = n_total - n_groups

            # Eta-squared
            grand_mean = float(np.mean(temp_df[dep_var]))
            ss_total = float(np.sum((temp_df[dep_var] - grand_mean) ** 2))
            ss_between = float(sum(
                len(arr) * (float(np.mean(arr)) - grand_mean) ** 2
                for arr in group_data if len(arr) > 0
            ))
            eta_sq = ss_between / ss_total if ss_total > 0 else 0.0
            effect_size = round(eta_sq, 4)
            effect_label = "η² (eta-squared)"
            df_val = df_between

            extra = {
                "degrees_of_freedom_between": df_between,
                "degrees_of_freedom_within": df_within,
                "k_groups": n_groups,
                "eta_squared": round(eta_sq, 4),
            }

        elif actual_method == "mann_whitney_u":
            g1, g2 = group_data[0], group_data[1]
            stat, p_val = stats.mannwhitneyu(g1, g2, alternative="two-sided")
            n1, n2 = len(g1), len(g2)
            # Rank-biserial correlation
            rbc = 1 - (2 * float(stat)) / (n1 * n2) if n1 * n2 > 0 else 0.0
            effect_size = round(abs(rbc), 4)
            effect_label = "r (rank-biserial)"

            extra = {
                "group1_label": str(groups_labels[0]),
                "group2_label": str(groups_labels[1]),
                "n_group1": n1,
                "n_group2": n2,
            }

        elif actual_method == "kruskal_wallis":
            stat, p_val = stats.kruskal(*group_data)
            # Epsilon-squared effect size
            H = float(stat)
            eps_sq = (H - n_groups + 1) / (n_total - n_groups) if n_total > n_groups else 0.0
            effect_size = round(max(0.0, eps_sq), 4)
            effect_label = "ε² (epsilon-squared)"

            extra = {
                "degrees_of_freedom": n_groups - 1,
                "k_groups": n_groups,
            }

        else:
            return {
                "dependent_var": dep_var,
                "grouping_var": grp_var,
                "method_used": actual_method,
                "n_total": n_total,
                "status": "error",
                "error_message": f"Method '{actual_method}' is not supported in batch engine."
            }

        return {
            "dependent_var": dep_var,
            "grouping_var": grp_var,
            "method_used": actual_method,
            "n_total": n_total,
            "n_groups": n_groups,
            "test_statistic": round(float(stat), 4) if stat is not None else None,
            "p_value": round(float(p_val), 4) if p_val is not None else None,
            "effect_size": effect_size,
            "effect_size_label": effect_label,
            "group_summaries": group_summaries,
            "status": "success",
            **extra
        }

    except Exception as e:
        return {
            "dependent_var": dep_var,
            "grouping_var": grp_var,
            "method_used": actual_method,
            "n_total": n_total,
            "n_groups": n_groups,
            "status": "error",
            "error_message": f"Computation failed: {str(e)}"
        }


def run_batch(
    data: pd.DataFrame,
    dep_vars: List[str],
    grp_vars: List[str],
    requested_method: str,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main entry point for batch execution.

    Parameters
    ----------
    data : pd.DataFrame  — the full dataset
    dep_vars : list of str  — one or more dependent (outcome) variable names
    grp_vars : list of str  — one or more grouping variable names
    requested_method : str  — the method ID the user selected (e.g. 'ttest_independent')
    options : dict — pass-through options (survey design, etc.)

    Returns
    -------
    dict with keys:
        rows          — list of BatchRow dicts (one per dep×grp combination)
        auto_corrections — list of auto-correction note strings
        is_batch      — True when more than one (dep, grp) pair was run
        n_comparisons — total number of pairs executed
        requested_method — original method requested by user
    """
    rows: List[BatchRow] = []
    auto_corrections: List[str] = []

    for dep in dep_vars:
        if not dep or dep not in data.columns:
            rows.append({
                "dependent_var": dep,
                "grouping_var": "—",
                "method_used": requested_method,
                "status": "error",
                "error_message": f"Dependent variable '{dep}' not found in dataset."
            })
            continue

        for grp in grp_vars:
            if not grp or grp not in data.columns:
                rows.append({
                    "dependent_var": dep,
                    "grouping_var": grp,
                    "method_used": requested_method,
                    "status": "error",
                    "error_message": f"Grouping variable '{grp}' not found in dataset."
                })
                continue

            n_groups = _get_group_count(data, grp)
            actual_method, correction_note = _auto_correct_method(requested_method, n_groups, grp)

            if correction_note and correction_note not in auto_corrections:
                auto_corrections.append(correction_note)

            row = _run_single_pair(data, dep, grp, actual_method, options)
            row["auto_corrected"] = correction_note is not None
            row["original_method_requested"] = requested_method
            rows.append(row)

    return {
        "rows": rows,
        "auto_corrections": auto_corrections,
        "is_batch": len(dep_vars) > 1 or len(grp_vars) > 1,
        "n_comparisons": len(rows),
        "requested_method": requested_method,
    }
