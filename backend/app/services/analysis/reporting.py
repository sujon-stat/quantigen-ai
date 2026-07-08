from typing import Any, Dict
from backend.app.services.statistics.base import MethodResult


class APAReportingService:
    """
    Generates exact American Psychological Association (APA 7th edition)
    publication reporting strings for statistical analysis results.
    """

    @staticmethod
    def _format_p(p_val: float) -> str:
        """Format p-value according to APA 7th edition standards (< .001 or exact without leading zero)."""
        if p_val is None:
            return "= .---"
        if p_val < 0.001:
            return "< .001"
        p_str = f"{p_val:.3f}"
        if p_str.startswith("0."):
            return f"= {p_str[1:]}"
        return f"= {p_str}"

    @classmethod
    def generate_apa_citation(cls, result: MethodResult) -> str:
        """
        Generate exact APA 7th edition reporting string based on method_id and results.
        """
        if not result or not result.main_results:
            return "No analysis results available for APA formatting."

        method_id = result.method_id
        main = result.main_results
        effect = result.effect_sizes or {}
        vars_used = result.variables_used or {}
        n = result.sample_size or 0

        p_val = main.get("p_value") if main.get("p_value") is not None else (
            main.get("f_p_value") if main.get("f_p_value") is not None else main.get("likelihood_ratio_p_value")
        )
        p_str = cls._format_p(p_val) if p_val is not None else ""
        sig_text = "a statistically significant" if (p_val is not None and p_val < 0.05) else "no statistically significant"

        if method_id == "descriptive":
            var_list = ", ".join(str(v) for v in vars_used.get("variables", []))
            return f"Descriptive statistics were calculated for {n} observations across target variables ({var_list})."

        elif method_id == "ttest_independent":
            dep = vars_used.get("dependent", "DV")
            grp = vars_used.get("grouping", "Group")
            t_stat = main.get("t_statistic", 0.0)
            df = main.get("degrees_of_freedom", n - 2)
            d = effect.get("cohens_d", 0.0)
            ci_l = effect.get("d_ci_lower", 0.0)
            ci_u = effect.get("d_ci_upper", 0.0)
            return (
                f"An independent-samples t-test revealed {sig_text} difference in {dep} across {grp} groups, "
                f"t({df:.2f}) = {t_stat:.2f}, p {p_str}, Cohen's d = {d:.2f}, 95% CI [{ci_l:.2f}, {ci_u:.2f}]."
            )

        elif method_id == "pearson_correlation":
            v1 = vars_used.get("var1", "Variable 1")
            v2 = vars_used.get("var2", "Variable 2")
            r = main.get("correlation_coefficient", 0.0)
            df = main.get("degrees_of_freedom", n - 2)
            ci_l = effect.get("ci_95_lower", 0.0)
            ci_u = effect.get("ci_95_upper", 0.0)
            return (
                f"A Pearson product-moment correlation coefficient was computed to assess the linear relationship between {v1} and {v2}. "
                f"There was {sig_text} correlation, r({df}) = {r:.2f}, p {p_str}, 95% CI [{ci_l:.2f}, {ci_u:.2f}]."
            )

        elif method_id == "chi_square_independence":
            v1 = vars_used.get("var1", "Variable 1")
            v2 = vars_used.get("var2", "Variable 2")
            chi2 = main.get("chi2_statistic", 0.0)
            df = main.get("degrees_of_freedom", 1)
            v = effect.get("cramers_v", 0.0)
            return (
                f"A Pearson chi-square test of independence was conducted to examine the association between {v1} and {v2}. "
                f"The results indicated {sig_text} association, \u03c7\u00b2({df}, N = {n}) = {chi2:.2f}, p {p_str}, Cramer's V = {v:.2f}."
            )

        elif method_id == "linear_regression":
            x = vars_used.get("independent", "Predictor")
            y = vars_used.get("dependent", "Outcome")
            f_stat = main.get("f_statistic", 0.0)
            r2 = main.get("r_squared", 0.0)
            return (
                f"A simple linear regression was conducted to evaluate whether {x} significantly predicted {y}. "
                f"The regression model was {'statistically significant' if p_val is not None and p_val < 0.05 else 'not statistically significant'}, "
                f"F(1, {n - 2}) = {f_stat:.2f}, p {p_str}, explaining {r2 * 100:.1f}% of the variance (R\u00b2 = {r2:.2f})."
            )

        elif method_id == "anova_oneway":
            dep = vars_used.get("dependent", "DV")
            grp = vars_used.get("grouping", "Group")
            f_stat = main.get("f_statistic", 0.0)
            df_m = main.get("df_between", 1)
            df_r = main.get("df_within", n - 2)
            eta = effect.get("eta_squared", 0.0)
            return (
                f"A one-way analysis of variance (ANOVA) showed {sig_text} main effect of {grp} on {dep}, "
                f"F({df_m}, {df_r}) = {f_stat:.2f}, p {p_str}, \u03b7\u00b2 = {eta:.2f}."
            )

        elif method_id == "mann_whitney_u":
            dep = vars_used.get("dependent", "DV")
            grp = vars_used.get("grouping", "Group")
            u_stat = main.get("u_statistic", 0.0)
            rb = effect.get("rank_biserial_correlation", 0.0)
            return (
                f"A Mann-Whitney U test indicated {sig_text} difference in the distribution of {dep} between {grp} categories, "
                f"U = {u_stat:.2f}, p {p_str}, rank-biserial correlation r_B = {rb:.2f}."
            )

        elif method_id == "kruskal_wallis":
            dep = vars_used.get("dependent", "DV")
            grp = vars_used.get("grouping", "Group")
            h_stat = main.get("h_statistic", 0.0)
            df = main.get("degrees_of_freedom", 1)
            eps = effect.get("epsilon_squared", 0.0)
            return (
                f"A Kruskal-Wallis H test revealed {sig_text} difference in {dep} across {grp} groups, "
                f"H({df}) = {h_stat:.2f}, p {p_str}, \u03b5\u00b2 = {eps:.2f}."
            )

        elif method_id == "multiple_linear_regression":
            dep = vars_used.get("dependent", "DV")
            ind_list = vars_used.get("independent", [])
            f_stat = main.get("f_statistic", 0.0)
            df_m = main.get("dof_model", len(ind_list) if isinstance(ind_list, list) else 1)
            df_r = main.get("dof_residual", n - int(df_m) - 1)
            r2 = main.get("r_squared", 0.0)
            r2_adj = main.get("adjusted_r_squared", 0.0)
            return (
                f"Multiple linear regression was calculated to predict {dep} based on predictors ({', '.join(ind_list) if isinstance(ind_list, list) else str(ind_list)}). "
                f"The overall regression equation was {'significant' if p_val is not None and p_val < 0.05 else 'not significant'}, "
                f"F({int(df_m)}, {int(df_r)}) = {f_stat:.2f}, p {p_str}, with R\u00b2 = {r2:.2f} (Adjusted R\u00b2 = {r2_adj:.2f})."
            )

        elif method_id == "binary_logistic_regression":
            dep = vars_used.get("dependent", "DV")
            ind_list = vars_used.get("independent", [])
            chi2 = main.get("likelihood_ratio_chi2", 0.0)
            df_m = main.get("dof_model", len(ind_list) if isinstance(ind_list, list) else 1)
            r2 = main.get("mcfadden_pseudo_r_squared", 0.0)
            return (
                f"A binary logistic regression model was fitted to predict the log odds of {dep} using {', '.join(ind_list) if isinstance(ind_list, list) else str(ind_list)}. "
                f"The model evaluation yielded a Likelihood Ratio \u03c7\u00b2({int(df_m)}) = {chi2:.2f}, p {p_str}, with McFadden's R\u00b2 = {r2:.2f}."
            )

        return f"Statistical analysis completed using {result.method_name} (n = {n}, p {p_str})."
