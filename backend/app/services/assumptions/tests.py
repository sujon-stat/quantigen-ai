import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson
from statsmodels.stats.outliers_influence import variance_inflation_factor
from typing import Any, Dict, List, Tuple


def test_shapiro_wilk(data: pd.Series) -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Run Shapiro-Wilk test for normality on a numeric series.
    Returns: (passed, test_statistic, p_value, details)
    """
    clean_data = data.dropna()
    n = len(clean_data)
    if n < 3:
        return False, 0.0, 0.0, {"error": "Sample size too small for Shapiro-Wilk test (n < 3)", "sample_size": n}
    
    # Shapiro-Wilk has max N limit of 5000 in scipy
    sample = clean_data.sample(min(n, 5000), random_state=42) if n > 5000 else clean_data
    stat, p = stats.shapiro(sample)
    passed = bool(p >= 0.05)
    return passed, float(stat), float(p), {"sample_size": n, "subsampled": n > 5000}


def test_levene_homogeneity(group_series_list: List[pd.Series]) -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Run Levene's test for equal variances across multiple group series.
    Returns: (passed, test_statistic, p_value, details)
    """
    clean_groups = [g.dropna() for g in group_series_list if len(g.dropna()) > 1]
    if len(clean_groups) < 2:
        return False, 0.0, 0.0, {"error": "Need at least two groups with >1 observation for Levene's test"}
    
    stat, p = stats.levene(*clean_groups, center='median')
    passed = bool(p >= 0.05)
    group_sizes = [len(g) for g in clean_groups]
    max_min_ratio = max(group_sizes) / min(group_sizes) if min(group_sizes) > 0 else 999.0
    
    return passed, float(stat), float(p), {
        "group_sizes": group_sizes,
        "unequal_group_sizes": max_min_ratio > 1.5,
        "size_ratio": float(max_min_ratio)
    }


def test_iqr_outliers(data: pd.Series, multiplier: float = 3.0) -> Tuple[bool, float, Optional[float], Dict[str, Any]]:
    """
    Check for extreme outliers using IQR method (default 3.0 * IQR for extreme outliers).
    Returns: (passed, outlier_count, None, details)
    """
    clean_data = data.dropna()
    n = len(clean_data)
    if n == 0:
        return False, 0.0, None, {"error": "No observations available"}
    
    q25, q75 = np.percentile(clean_data, [25, 75])
    iqr = q75 - q25
    lower_bound = q25 - multiplier * iqr
    upper_bound = q75 + multiplier * iqr
    
    outliers = clean_data[(clean_data < lower_bound) | (clean_data > upper_bound)]
    outlier_count = len(outliers)
    passed = bool(outlier_count == 0)
    
    return passed, float(outlier_count), None, {
        "sample_size": n,
        "outlier_count": outlier_count,
        "outlier_percentage": float((outlier_count / n) * 100) if n > 0 else 0.0,
        "bounds": [float(lower_bound), float(upper_bound)]
    }


def test_expected_cell_frequencies(contingency_table: pd.DataFrame) -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Check if expected cell frequencies in a contingency table are all >= 5.
    Returns: (passed, min_expected_freq, proportion_below_5, details)
    """
    if contingency_table.empty or contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
        return False, 0.0, 1.0, {"error": "Contingency table must be at least 2x2"}
    
    chi2, p, dof, expected = stats.chi2_contingency(contingency_table)
    min_expected = float(np.min(expected))
    cells_below_5 = int(np.sum(expected < 5.0))
    total_cells = expected.size
    prop_below_5 = float(cells_below_5 / total_cells)
    
    passed = bool(cells_below_5 == 0)
    
    return passed, min_expected, prop_below_5, {
        "min_expected": min_expected,
        "cells_below_5": cells_below_5,
        "total_cells": total_cells,
        "is_2x2": contingency_table.shape == (2, 2)
    }


def test_breusch_pagan(y: pd.Series, X: pd.DataFrame) -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Check for homoscedasticity using Breusch-Pagan test.
    Returns: (passed, lm_stat, lm_pvalue, details)
    """
    # Align indices and drop NAs
    df_aligned = pd.concat([y, X], axis=1).dropna()
    if df_aligned.shape[0] < X.shape[1] + 2:
        return False, 0.0, 0.0, {"error": "Insufficient observations for Breusch-Pagan test"}
    
    y_clean = df_aligned.iloc[:, 0]
    X_clean = sm.add_constant(df_aligned.iloc[:, 1:])
    
    model = sm.OLS(y_clean, X_clean).fit()
    bp_stat, bp_pvalue, f_stat, f_pvalue = het_breuschpagan(model.resid, model.model.exog)
    
    passed = bool(bp_pvalue >= 0.05)
    return passed, float(bp_stat), float(bp_pvalue), {"f_stat": float(f_stat), "f_pvalue": float(f_pvalue)}


def test_durbin_watson_autocorrelation(residuals: pd.Series) -> Tuple[bool, float, Optional[float], Dict[str, Any]]:
    """
    Check Durbin-Watson statistic for autocorrelation of residuals.
    Ideal is 2.0; range [1.5, 2.5] is generally acceptable (passed).
    Returns: (passed, dw_statistic, None, details)
    """
    clean_resid = residuals.dropna()
    if len(clean_resid) < 3:
        return False, 0.0, None, {"error": "Insufficient residuals for Durbin-Watson check"}
    
    dw_stat = float(durbin_watson(clean_resid))
    passed = bool(1.5 <= dw_stat <= 2.5)
    
    return passed, dw_stat, None, {
        "dw_statistic": dw_stat,
        "interpretation": "Positive autocorrelation" if dw_stat < 1.5 else ("Negative autocorrelation" if dw_stat > 2.5 else "No severe autocorrelation")
    }


def test_cooks_distance(y: pd.Series, X: pd.DataFrame) -> Tuple[bool, float, Optional[float], Dict[str, Any]]:
    """
    Identify influential points using Cook's Distance > 4/n.
    Returns: (passed, influential_count, max_cooks_d, details)
    """
    df_aligned = pd.concat([y, X], axis=1).dropna()
    n = df_aligned.shape[0]
    if n < X.shape[1] + 3:
        return False, 0.0, None, {"error": "Insufficient observations for Cook's Distance check"}
    
    y_clean = df_aligned.iloc[:, 0]
    X_clean = sm.add_constant(df_aligned.iloc[:, 1:])
    
    model = sm.OLS(y_clean, X_clean).fit()
    influence = model.get_influence()
    cooks_d, _ = influence.cooks_distance
    
    threshold = 4.0 / n
    influential_points = int(np.sum(cooks_d > threshold))
    max_d = float(np.max(cooks_d)) if len(cooks_d) > 0 else 0.0
    passed = bool(influential_points == 0)
    
    return passed, float(influential_points), max_d, {
        "sample_size": n,
        "threshold": threshold,
        "influential_count": influential_points,
        "max_cooks_distance": max_d
    }


def test_vif_multicollinearity(X: pd.DataFrame) -> Tuple[bool, float, Optional[float], Dict[str, Any]]:
    """
    Check Variance Inflation Factor (VIF) for multicollinearity across predictors.
    Returns: (passed, max_vif, None, details)
    """
    clean_X = X.select_dtypes(include=[np.number]).dropna()
    if clean_X.shape[1] <= 1:
        # If only 1 predictor, multicollinearity is impossible
        return True, 1.0, None, {"max_vif": 1.0, "vif_values": {}}
    
    # Add constant for VIF calculation if not present
    X_const = sm.add_constant(clean_X)
    vif_dict = {}
    for i in range(1, X_const.shape[1]):  # skip intercept column
        col_name = X_const.columns[i]
        try:
            vif = float(variance_inflation_factor(X_const.values, i))
            vif_dict[col_name] = vif
        except Exception:
            vif_dict[col_name] = 999.0
            
    max_vif = max(vif_dict.values()) if vif_dict else 1.0
    passed = bool(max_vif < 10.0)
    
    return passed, float(max_vif), None, {"max_vif": float(max_vif), "vif_values": vif_dict}


def test_binary_outcome(data: pd.Series) -> Tuple[bool, float, Optional[float], Dict[str, Any]]:
    """
    Check if a dependent variable is strictly binary (exactly 2 unique values).
    Returns: (passed, unique_count, None, details)
    """
    clean_data = data.dropna()
    unique_vals = clean_data.unique()
    unique_count = len(unique_vals)
    passed = bool(unique_count == 2)
    
    return passed, float(unique_count), None, {
        "unique_count": unique_count,
        "unique_values": [str(x) for x in unique_vals[:10]],
        "is_binary": passed
    }


def test_residuals_normality(y: pd.Series, X: pd.DataFrame) -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Fit a linear model and test normality of residuals using Shapiro-Wilk.
    Returns: (passed, shapiro_stat, p_value, details)
    """
    df_aligned = pd.concat([y, X], axis=1).dropna()
    if df_aligned.shape[0] < X.shape[1] + 3:
        return False, 0.0, 0.0, {"error": "Insufficient observations to check residual normality"}
        
    y_clean = df_aligned.iloc[:, 0]
    X_clean = sm.add_constant(df_aligned.iloc[:, 1:].select_dtypes(include=[np.number]))
    
    try:
        model = sm.OLS(y_clean, X_clean).fit()
        residuals = pd.Series(model.resid)
        passed, stat, p, details = test_shapiro_wilk(residuals)
        details["residual_std"] = float(residuals.std())
        return passed, stat, p, details
    except Exception as e:
        return False, 0.0, 0.0, {"error": f"Failed to compute model residuals: {str(e)}"}
