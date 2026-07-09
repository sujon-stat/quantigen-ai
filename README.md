---
title: Quantigen AI — No-Code Statistical Platform
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
pinned: true
license: mit
---

<div align="center">
  # Quantigen AI
  
  **The Agentic No-Code Statistical Platform**
  
  *Reliability Over Intelligence • Assumption-First Transparency*
  
  [![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://python.org)
  [![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

  <br />

  <a href="https://huggingface.co/spaces/sujon-stat/quantigen-ai"><strong>🌐 Live Cloud Demo</strong></a> • 
  <a href="https://github.com/sujon-stat/quantigen-ai#"><strong>📖 Documentation</strong></a> • 
  <a href="https://github.com/sujon-stat/quantigen-ai/issues"><strong>🐞 Report Bug</strong></a>
</div>

---

## 🧠 The Problem with Current AI Tools
Tools like ChatGPT Code Interpreter or Julius AI are powerful, but they treat statistics like a text-generation problem. They frequently:
- **Hallucinate p-values** or use the wrong statistical tests.
- **Ignore assumptions** (e.g., running a T-test on non-normal data without warning).
- **Provide no transparency** (you can't verify how they got the exact mathematical result).
- Require prompt engineering instead of methodological rigor.

## 🛡️ The Quantigen Solution
Quantigen AI is an **Agentic Statistical Engineer**, not just a chatbot. It bridges the gap between the raw computational power of R/Python and the point-and-click usability of GUI tools like SPSS, reinforced with built-in AI guidance.

### Core Pillars
1. 🛡️ **Assumption-First Diagnostic Shield:** Before calculating *any* p-value, Quantigen automatically runs rigorous Shapiro-Wilk normality, Levene's homogeneity of variance, and VIF multicollinearity checks. If violated, it flags the issue, explains it in plain English, and auto-applies robust corrections (such as Welch's degrees of freedom or HC3 heteroscedasticity-consistent standard errors).
2. 🔬 **Reliability Over Intelligence:** We use LLMs for natural language parsing and bilingual rationale, but we use hardened, verified Python (`scipy`, `statsmodels`) and native R (`rpy2` + `r-base-core`) templates to execute the math. Zero hallucinated statistics.
3. 💻 **Full R & Python Transparency:** Every single analysis generates the exact, reproducible `.R` and `.py` code blocks right alongside the output.
4. 📊 **Publication-Ready Suite:** APA 7th Edition formatted narrative results with instant 4-format download (`.doc`, `.pdf`, `.html`, `.md`) and high-res (300 DPI) static + interactive Plotly visualizations.

## 🚀 Verified Statistical & Regression Registry (10 Methods)
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

## ⚙️ Tech Stack & Architecture
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons, Plotly.js (`react-plotly.js`) with living multi-state `QuantigenLogo` Q-Core.
- **Backend:** Python 3.12, FastAPI, Pydantic v2, SciPy, Statsmodels, Scikit-learn, Kaleido 300 DPI engine.
- **R Engine Integration:** Jinja2 & native `rpy2` (`r-base-core`) executing verified `.R` statistical scripts.
- **AI/NL Consultant:** Natural Language hypothesis parser (`POST /api/v1/chat/recommend`) with bilingual clinical/business rationale.
- **Cloud Deployment:** Hugging Face Spaces & Docker (Single-port 8000 unified deployment).

## 🗺️ Roadmap & Strategic Differentiation
- [x] Phase 0: Core UI, Smart Data Profiling, Auto-Type Inference & Measurement Scale Registry
- [x] Phase 1: T-Test, Correlation, Chi-Square with Assumption Shield & Auto-Corrections
- [x] Phase 2: ANOVA, Multiple & Logistic Regression, Native R Script & Python Code Generation
- [x] Phase 3: Publication Suite (DOC, PDF, HTML, MD) & Interactive Multi-State Q-Core Engine Logo
- [ ] **Phase 4: Survey-Weighted Statistical Engine (SurveyNCD Integration)** — *The Unmatched Niche:* Adding complex survey design awareness (sample weights, primary sampling units/clusters, and stratification) across all 10 classical statistical & regression methods (`survey::svydesign`, `statsmodels.stats.weightstats`). Tailored specifically for public health and population researchers analyzing **DHS, MICS, and WHO STEPS** datasets.
- [ ] Phase 5: Advanced ML Models (Random Forest, XGBoost) with SHAP Explainable AI (XAI)
- [ ] Phase 6: Full Agentic Data Autocleaning & Transformation Pipelines

## 🛠️ Local Development & Setup

### Folder Structure
```text
quantigen-ai/
│
├── frontend/                 # React/Vite/TypeScript glassmorphic studio
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                  # FastAPI/Python statistical & R engine
│   ├── app/
│   ├── tests/
│   └── main.py
│
├── r_templates/              # Verified Jinja2 R execution templates
├── Dockerfile                # Multi-stage production container build
├── .gitignore                # Security hard-locked git exclusion rules
├── LICENSE                   # MIT License
├── CONTRIBUTING.md           # Contribution & PR guidelines
└── README.md                 # Project documentation & investor pitch
```

### Setup Backend Engine
```bash
python -m venv venv
venv\Scripts\activate
pip install -e .[dev]
uvicorn backend.app.main:app --reload --port 8000
```

### Setup Frontend Studio
```bash
cd frontend
npm install
npm run dev
```

## 🤝 Contributing
Quantigen AI is an open-source project designed to set the world standard for trustworthy statistical AI and complex survey analysis. We welcome contributions, especially to our statistical assumption rules database, survey design (`svydesign`) integrations, and R execution templates! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
<div align="center">
  Built with ❤️ in Bangladesh | Powered by Math, Not Magic
</div>
