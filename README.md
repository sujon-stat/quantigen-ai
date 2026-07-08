---
title: StatMind AI — No-Code Statistical Platform
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
pinned: true
license: mit
---

# StatMind AI — No-Code Statistical Analysis Platform

A web-based statistical analysis software that works like R/Python but requires **ZERO coding**. Users upload datasets, select variables and methods (or use natural language), and get professional results with full transparency, assumption validation, and educational guidance.

## Core Principles
1. **RELIABILITY OVER INTELLIGENCE**: A correct simple answer beats a wrong sophisticated answer.
2. **TRANSPARENCY**: Every analysis shows exact R/Python code, statistical procedures, and assumptions checked.
3. **ASSUMPTION-FIRST**: Before running ANY method, assumptions are verified. If violated, users receive warnings with explanations and suggested remedies BEFORE showing results.
4. **EDUCATION-EMBEDDED**: Every output teaches what the statistics mean in real-world context.
5. **NEVER AUTO-EXECUTE HARMFUL OPERATIONS**: Deletion and data modifications require strict user confirmation.

## Tech Stack
- **Backend**: Python 3.12+, FastAPI, Pydantic v2
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons, Plotly.js (`react-plotly.js`)
- **Statistics Engine**: `scipy`, `statsmodels`, `scikit-learn`, `numpy`, `pandas`
- **R Integration**: Jinja2 & native `rpy2` (`r-base-core`) for clean educational R code templates and execution validation
- **Visualizations & Export**: Plotly (`plotly.graph_objects`) with `STATMIND_THEME` + `kaleido` for 300 DPI publication static PNG figures and HTML manuscripts
- **AI/NL Consultant**: Natural Language hypothesis parser (`POST /api/v1/chat/recommend`) with bilingual rationale

## Verified Statistical & Regression Registry (10 Methods)
1. **Descriptive Statistics**: Comprehensive data profiling, skewness, kurtosis, and missingness checks.
2. **Independent Samples T-Test**: Welch's equal/unequal variance auto-correction, Cohen's d effect size, normality checks.
3. **Pearson Correlation**: Exact p-values, Fisher Z confidence intervals, linearity/bivariate checks.
4. **Chi-Square Test of Independence**: Cramer's V effect size, expected cell frequency diagnostics.
5. **Simple Linear Regression**: OLS regression, ANOVA table, Durbin-Watson, Breusch-Pagan homoscedasticity auto-fix (`HC3`).
6. **One-Way ANOVA**: Classic Fisher vs. Welch ANOVA auto-switch upon Levene homogeneity violations.
7. **Mann-Whitney U Test**: Non-parametric two-group comparison with exact rank-biserial correlation effect size.
8. **Kruskal-Wallis H Test**: Non-parametric multi-group comparison with Bonferroni Dunn post-hoc adjustments.
9. **Multiple Linear Regression**: Multi-variable OLS with Variance Inflation Factor (`VIF`) multicollinearity checks.
10. **Binary Logistic Regression**: Maximum likelihood estimation with exact Odds Ratios (`OR`), 95% CI, and McFadden's R².

## Getting Started

### Local Backend Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -e .[dev]
uvicorn backend.app.main:app --reload
```

### Run Tests
```bash
pytest tests/ -v
```
