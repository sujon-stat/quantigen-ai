from typing import Dict, List
from backend.app.models.assumptions import AssumptionRule, Severity


TTEST_INDEPENDENT_RULES: List[AssumptionRule] = [
    AssumptionRule(
        name="sample_size",
        description="Sufficient sample size per group",
        test_name="group_sample_size_check",
        threshold=5.0,
        severity=Severity.ERROR,
        consequence="Small sample sizes (<5 per group) prevent reliable estimation of group variances and standard errors.",
        remedy="Collect more observations or merge small subgroups before conducting a parametric t-test."
    ),
    AssumptionRule(
        name="continuous_dv",
        description="Continuous dependent variable",
        test_name="variable_type_check",
        severity=Severity.ERROR,
        consequence="T-test compares means, which are statistically meaningless for ordinal or nominal categorical data.",
        remedy="If your outcome is ordinal (e.g. Likert scale) or ranked, use the Mann-Whitney U test instead."
    ),
    AssumptionRule(
        name="independence",
        description="Independent observations between groups",
        test_name="design_check",
        severity=Severity.ERROR,
        consequence="Violating independence inflates Type I error rate dramatically and invalidates standard error calculations.",
        remedy="If measurements are from the same subjects (e.g., before/after), use a Paired Samples T-Test instead."
    ),
    AssumptionRule(
        name="normality",
        description="Normality of sampling distribution per group",
        test_name="shapiro_wilk",
        threshold=0.05,
        severity=Severity.WARNING,
        consequence="Non-normal distributions can distort p-values in small samples (n < 30).",
        remedy="For large samples (n > 30), the Central Limit Theorem ensures robustness. For small samples, consider the non-parametric Mann-Whitney U test or log/Box-Cox transformation.",
        alternative_method="mann_whitney_u"
    ),
    AssumptionRule(
        name="homogeneity_variance",
        description="Homogeneity of variance across groups (Equal Variances)",
        test_name="levene",
        threshold=0.05,
        severity=Severity.AUTO_FIX,
        consequence="Unequal variances bias the pooled standard error, especially when sample sizes across groups are unequal.",
        remedy="Switching to Welch's t-test, which adjusts degrees of freedom and does not assume equal variances.",
        auto_fix_action="welch_ttest"
    ),
    AssumptionRule(
        name="outliers",
        description="No extreme outliers in dependent variable within groups",
        test_name="iqr_outliers",
        threshold=3.0,
        severity=Severity.WARNING,
        consequence="Extreme outliers disproportionately shift the sample mean and inflate sample standard deviation, reducing test power.",
        remedy="Examine the boxplot/violin plot. Verify data entry accuracy, or report sensitivity results both with and without extreme outliers."
    )
]


CORRELATION_PEARSON_RULES: List[AssumptionRule] = [
    AssumptionRule(
        name="continuous_variables",
        description="Both variables must be continuous numeric scales",
        test_name="variable_type_check",
        severity=Severity.ERROR,
        consequence="Pearson correlation calculates linear covariance between metric scales. Categorical variables invalidate the metric.",
        remedy="If one or both variables are ordinal ranks or skewed scores, use Spearman's rank-order correlation."
    ),
    AssumptionRule(
        name="sample_size",
        description="Sufficient paired observations",
        test_name="sample_size_check",
        threshold=5.0,
        severity=Severity.ERROR,
        consequence="Correlations estimated from fewer than 5 pairs are highly unstable and prone to spurious associations.",
        remedy="Gather additional paired observations before testing correlation."
    ),
    AssumptionRule(
        name="bivariate_normality",
        description="Bivariate normality of the paired variables",
        test_name="shapiro_wilk_bivariate",
        threshold=0.05,
        severity=Severity.WARNING,
        consequence="Violation of normality invalidates the exact parametric p-value and confidence interval bounds when n is small.",
        remedy="With large n (>50), Pearson r is robust. For heavy tails or severe skew, use Spearman's rank correlation.",
        alternative_method="correlation_spearman"
    ),
    AssumptionRule(
        name="outliers",
        description="No extreme bivariate or univariate outliers",
        test_name="iqr_outliers_both",
        threshold=3.0,
        severity=Severity.WARNING,
        consequence="A single extreme leverage point can artificially create or completely obscure a strong correlation.",
        remedy="Inspect the scatter plot. Check outlier validity and consider reporting Pearson r both with and without influential points."
    ),
    AssumptionRule(
        name="linearity",
        description="Linear relationship between X and Y",
        test_name="visual_scatter_check",
        severity=Severity.WARNING,
        consequence="Pearson r specifically measures linear co-movement. If the relationship is curved (e.g., quadratic), r may equal 0 despite strong association.",
        remedy="Examine the scatter plot and polynomial fit. If monotonic but curved, switch to Spearman correlation."
    )
]


CHI_SQUARE_RULES: List[AssumptionRule] = [
    AssumptionRule(
        name="categorical_variables",
        description="Both variables must be categorical (nominal or ordinal)",
        test_name="variable_type_check",
        severity=Severity.ERROR,
        consequence="Chi-Square tests evaluate cross-tabulated frequency counts across discrete categories.",
        remedy="If your variables are continuous numeric scales, bin/discretize them into meaningful categories or use regression/correlation instead."
    ),
    AssumptionRule(
        name="independent_observations",
        description="Independent observations across contingency table cells",
        test_name="design_check",
        severity=Severity.ERROR,
        consequence="Each participant or entity must contribute to exactly ONE cell in the table. Repeated measures invalidate the multinomial distribution.",
        remedy="If participants appear in multiple categories over time or conditions, use McNemar's test or generalized estimating equations."
    ),
    AssumptionRule(
        name="minimum_sample_size",
        description="Overall sample size adequacy (n >= 20)",
        test_name="sample_size_check",
        threshold=20.0,
        severity=Severity.ERROR,
        consequence="Chi-Square approximation to the discrete hypergeometric sampling distribution breaks down drastically with small total sample size.",
        remedy="Increase sample size or collapse sparse categories."
    ),
    AssumptionRule(
        name="expected_frequencies",
        description="Expected frequencies >= 5 in all cells",
        test_name="expected_cell_frequencies",
        threshold=5.0,
        severity=Severity.ERROR,
        consequence="When expected cell counts fall below 5, the chi-square test statistic becomes inaccurate and Type I error rates surge.",
        remedy="For 2x2 contingency tables, use Fisher's Exact Test. For larger tables, collapse rare levels into combined categories."
    ),
    AssumptionRule(
        name="random_sampling",
        description="Random sampling from population",
        test_name="design_check",
        severity=Severity.WARNING,
        consequence="Non-random convenience sampling limits the generalizability of observed categorical associations.",
        remedy="Keep sampling methodology in mind when drawing broader population inferences."
    )
]


REGRESSION_SIMPLE_RULES: List[AssumptionRule] = [
    AssumptionRule(
        name="minimum_sample_size",
        description="Adequate sample size relative to predictors (n >= 10 * p)",
        test_name="regression_sample_size",
        threshold=10.0,
        severity=Severity.ERROR,
        consequence="Fitting regression models with too few observations relative to predictors leads to severe overfitting and unreliable slope estimates.",
        remedy="Ensure at least 10 observations per predictor variable."
    ),
    AssumptionRule(
        name="linearity",
        description="Linear relationship between predictor and outcome",
        test_name="visual_residual_fitted",
        severity=Severity.WARNING,
        consequence="If the true relationship is non-linear, OLS slope estimates will be biased and predictions inaccurate across different ranges.",
        remedy="Inspect residual vs. fitted plots. Add polynomial terms (e.g. X^2) or apply log transformations to linearize the curve."
    ),
    AssumptionRule(
        name="normality_residuals",
        description="Normality of regression residuals",
        test_name="shapiro_wilk_residuals",
        threshold=0.05,
        severity=Severity.WARNING,
        consequence="Non-normal residuals distort confidence intervals and p-values for slope coefficients in smaller samples.",
        remedy="With large sample sizes (n > 30), OLS coefficients remain unbiased and asymptotically normal due to CLT. Otherwise, consider bootstrapped confidence intervals or outcome transformation."
    ),
    AssumptionRule(
        name="homoscedasticity",
        description="Constant variance of residuals (Homoscedasticity)",
        test_name="breusch_pagan",
        threshold=0.05,
        severity=Severity.AUTO_FIX,
        consequence="Heteroscedasticity (funnel-shaped residuals) biases standard error calculations, making t-tests for coefficients unreliable.",
        remedy="Switching to heteroscedasticity-consistent robust standard errors (HC3), which corrects inference without changing slope estimates.",
        auto_fix_action="robust_se_hc3"
    ),
    AssumptionRule(
        name="autocorrelation",
        description="Independence of residuals across observations (No Autocorrelation)",
        test_name="durbin_watson",
        threshold=1.5, # We check between 1.5 and 2.5 in tests.py
        severity=Severity.WARNING,
        consequence="Correlated residuals (e.g. in time series data) cause standard errors to be severely underestimated, inflating significance claims.",
        remedy="If data is sequential or time-ordered, use time-series regression models (ARIMA) or include lagged variables."
    ),
    AssumptionRule(
        name="influential_points",
        description="No high-leverage influential points distorting the model",
        test_name="cooks_distance",
        threshold=4.0, # 4/n formula applied in tests.py
        severity=Severity.WARNING,
        consequence="A single high-leverage outlier can tilt the entire regression line, giving misleading slope and intercept estimates.",
        remedy="Identify observations with high Cook's Distance (> 4/n). Inspect data validity and compare model fit with and without those points."
    ),
    AssumptionRule(
        name="multicollinearity",
        description="No severe multicollinearity among predictors (VIF < 10)",
        test_name="vif_check",
        threshold=10.0,
        severity=Severity.ERROR,
        consequence="Collinear predictors make slope standard errors explode, rendering individual variable coefficients unstable and uninterpretable.",
        remedy="Remove redundant predictors with VIF > 10, or combine collinear features using Principal Component Analysis."
    )
]


ANOVA_ONEWAY_RULES: List[AssumptionRule] = [
    AssumptionRule(
        name="sample_size",
        description="Sufficient sample size per group (n >= 3)",
        test_name="group_sample_size_check",
        threshold=3.0,
        severity=Severity.ERROR,
        consequence="Extremely small group sizes prevent reliable variance estimation and F-test calculation.",
        remedy="Collect more data per group or combine small subgroups."
    ),
    AssumptionRule(
        name="continuous_dv",
        description="Continuous dependent variable",
        test_name="variable_type_check",
        severity=Severity.ERROR,
        consequence="ANOVA compares group means across a continuous outcome scale.",
        remedy="If your outcome is ordinal ranks or Likert scale, use the Kruskal-Wallis H test instead."
    ),
    AssumptionRule(
        name="independence",
        description="Independent observations between and within groups",
        test_name="design_check",
        severity=Severity.ERROR,
        consequence="Non-independent observations invalidate the F-distribution and inflate Type I error.",
        remedy="Ensure different subjects are assigned to distinct groups without overlap."
    ),
    AssumptionRule(
        name="normality",
        description="Normality of sampling distribution within groups",
        test_name="shapiro_wilk",
        threshold=0.05,
        severity=Severity.WARNING,
        consequence="Non-normal distributions within groups can affect F-test accuracy when sample sizes are small.",
        remedy="For large sample sizes (n > 30 per group), ANOVA is robust to non-normality. For small samples with severe skewness, use the Kruskal-Wallis test.",
        alternative_method="kruskal_wallis"
    ),
    AssumptionRule(
        name="homogeneity_variance",
        description="Homogeneity of variance across all groups",
        test_name="levene",
        threshold=0.05,
        severity=Severity.AUTO_FIX,
        consequence="Unequal group variances bias the pooled error term in One-Way ANOVA, especially with unequal group sizes.",
        remedy="Switching automatically to Welch's ANOVA, which does not assume equal variances across groups.",
        auto_fix_action="welch_anova"
    ),
    AssumptionRule(
        name="outliers",
        description="No extreme outliers within any group",
        test_name="iqr_outliers",
        threshold=3.0,
        severity=Severity.WARNING,
        consequence="Outliers skew group means and inflate within-group variance, reducing ANOVA power.",
        remedy="Inspect group boxplots. Check data accuracy or run Kruskal-Wallis as a sensitivity check."
    )
]


MANN_WHITNEY_RULES: List[AssumptionRule] = [
    AssumptionRule(
        name="sample_size",
        description="Adequate sample size per group (n >= 5 recommended)",
        test_name="group_sample_size_check",
        threshold=5.0,
        severity=Severity.WARNING,
        consequence="Very small samples limit the number of possible rank permutations and test sensitivity.",
        remedy="Interpret p-values carefully or collect additional observations."
    ),
    AssumptionRule(
        name="independence",
        description="Independent observations across the two groups",
        test_name="design_check",
        severity=Severity.ERROR,
        consequence="Mann-Whitney U assumes subjects are independent between the two groups.",
        remedy="If comparing paired measurements from the same subjects, use the Wilcoxon Signed-Rank test instead."
    )
]


KRUSKAL_WALLIS_RULES: List[AssumptionRule] = [
    AssumptionRule(
        name="sample_size",
        description="Adequate sample size per group (n >= 5 recommended)",
        test_name="group_sample_size_check",
        threshold=5.0,
        severity=Severity.WARNING,
        consequence="Small group sizes make the chi-square approximation for the H-statistic less precise.",
        remedy="Interpret p-values carefully with small samples."
    ),
    AssumptionRule(
        name="independence",
        description="Independent observations across all groups",
        test_name="design_check",
        severity=Severity.ERROR,
        consequence="Subjects must not be repeatedly tested or shared across multiple comparison groups.",
        remedy="Ensure each observation belongs to exactly one independent group."
    )
]


REGRESSION_MULTIPLE_RULES: List[AssumptionRule] = [
    AssumptionRule(
        name="minimum_sample_size",
        description="Adequate sample size relative to predictors (n >= 10 * p)",
        test_name="regression_sample_size",
        threshold=10.0,
        severity=Severity.ERROR,
        consequence="Fitting multiple regression with too few observations relative to predictors leads to severe overfitting and inflated R-squared.",
        remedy="Ensure at least 10 observations per predictor variable."
    ),
    AssumptionRule(
        name="multicollinearity",
        description="No severe multicollinearity among predictors (VIF < 10)",
        test_name="vif_check",
        threshold=10.0,
        severity=Severity.ERROR,
        consequence="Multicollinearity inflates standard errors, making individual predictor p-values and coefficients highly unstable.",
        remedy="Remove redundant predictors with VIF > 10 or combine collinear features."
    ),
    AssumptionRule(
        name="normality_residuals",
        description="Normality of model residuals",
        test_name="shapiro_wilk_residuals",
        threshold=0.05,
        severity=Severity.WARNING,
        consequence="Non-normal residuals distort p-value and confidence interval estimation for regression coefficients in small samples.",
        remedy="With large samples (n > 30), OLS coefficients remain asymptotically normal. Otherwise, consider log-transforming skewed variables."
    ),
    AssumptionRule(
        name="homoscedasticity",
        description="Constant variance of residuals (Homoscedasticity)",
        test_name="breusch_pagan",
        threshold=0.05,
        severity=Severity.AUTO_FIX,
        consequence="Heteroscedasticity biases standard error calculations across predictors.",
        remedy="Switching automatically to heteroscedasticity-consistent robust standard errors (HC3).",
        auto_fix_action="robust_se_hc3"
    ),
    AssumptionRule(
        name="autocorrelation",
        description="Independence of residuals across observations",
        test_name="durbin_watson",
        threshold=1.5,
        severity=Severity.WARNING,
        consequence="Autocorrelated residuals underestimate standard errors and overstate significance.",
        remedy="Check whether observations are ordered sequentially or in time."
    ),
    AssumptionRule(
        name="influential_points",
        description="No high-leverage influential observations",
        test_name="cooks_distance",
        threshold=4.0,
        severity=Severity.WARNING,
        consequence="High-leverage outliers can pull regression hyperplanes and distort parameter estimates.",
        remedy="Identify points with high Cook's Distance (> 4/n) and verify data entry accuracy."
    )
]


REGRESSION_LOGISTIC_RULES: List[AssumptionRule] = [
    AssumptionRule(
        name="binary_outcome",
        description="Dependent variable must be strictly binary (exactly 2 categories)",
        test_name="binary_outcome_check",
        severity=Severity.ERROR,
        consequence="Binary logistic regression models the log-odds of a dichotomous (0 vs 1) event.",
        remedy="Ensure your dependent variable has exactly two categories (e.g. 0 and 1, or Yes and No)."
    ),
    AssumptionRule(
        name="minimum_sample_size",
        description="Adequate events per predictor variable (n >= 10 * p)",
        test_name="regression_sample_size",
        threshold=10.0,
        severity=Severity.ERROR,
        consequence="Logistic regression requires sufficient events per predictor to prevent separation and infinite log-odds estimates.",
        remedy="Ensure at least 10 observations per independent predictor variable."
    ),
    AssumptionRule(
        name="multicollinearity",
        description="No severe multicollinearity among independent predictors (VIF < 10)",
        test_name="vif_check",
        threshold=10.0,
        severity=Severity.ERROR,
        consequence="Multicollinearity makes Odds Ratio estimates unstable and inflates standard errors.",
        remedy="Remove redundant independent predictors with VIF > 10."
    ),
    AssumptionRule(
        name="influential_points",
        description="No extreme influential points in logistic space",
        test_name="cooks_distance",
        threshold=4.0,
        severity=Severity.WARNING,
        consequence="Extreme outliers can distort maximum likelihood parameter convergence.",
        remedy="Inspect high Cook's Distance points for data entry anomalies."
    )
]


METHOD_RULES_REGISTRY: Dict[str, List[AssumptionRule]] = {
    "ttest_independent": TTEST_INDEPENDENT_RULES,
    "correlation_pearson": CORRELATION_PEARSON_RULES,
    "chi_square_independence": CHI_SQUARE_RULES,
    "regression_simple": REGRESSION_SIMPLE_RULES,
    "descriptive_stats": [], # Descriptive statistics don't have inferential assumptions
    "anova_oneway": ANOVA_ONEWAY_RULES,
    "mann_whitney_u": MANN_WHITNEY_RULES,
    "kruskal_wallis": KRUSKAL_WALLIS_RULES,
    "regression_linear_multiple": REGRESSION_MULTIPLE_RULES,
    "regression_logistic": REGRESSION_LOGISTIC_RULES,
}


def get_rules_for_method(method_id: str) -> List[AssumptionRule]:
    """Retrieve all assumption rules for a given method ID."""
    return METHOD_RULES_REGISTRY.get(method_id, [])
