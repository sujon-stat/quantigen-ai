# Contributing to Quantigen AI

First off, thank you for considering contributing to **Quantigen AI**! It is people like you who make open-source software such a powerful tool for researchers, data scientists, and students around the world.

Our mission is simple: **Reliability Over Intelligence**. While most AI data analysis tools treat statistics like a text-generation problem and hallucinate $p$-values without checking assumptions, Quantigen enforces a rigorous **Assumption-First Diagnostic Shield** and native execution engines (Python & R) before delivering any inference.

---

## 🌟 Where We Need the Most Help: The Open Niche (Survey-Weighted Statistics)

Right now, tools like Julius AI, DataStatPro, and ChatGPT do "assumption-first classical stats with a chat layer" in a crowded market. **Our biggest strategic frontier where NO tool currently matches us is Complex Survey Design Awareness (`SurveyNCD` / DHS / MICS / STEPS integration).**

We are actively seeking contributors to help us expand our 10 verified statistical and regression methods to natively support:
- **Sample Weights (`probability weights / sampling weights`)**
- **Primary Sampling Units (PSUs / Clusters)**
- **Stratification & Finite Population Corrections (FPC)**
- **Survey Adapters (`survey::svydesign` in R and `statsmodels.stats.weightstats` in Python)**

If you have experience working with **DHS (Demographic and Health Surveys), UNICEF MICS, or WHO STEPS** public health datasets, your contributions here will directly impact thousands of epidemiological and demographic researchers globally.

---

## 🛠️ Development Setup

### 1. Fork & Clone the Repository
```bash
git clone https://github.com/your-username/quantigen-ai.git
cd quantigen-ai
```

### 2. Backend Setup (Python 3.12+ & FastAPI)
We use `uv` / standard `venv` for fast, reproducible dependency management:
```bash
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On macOS/Linux: source .venv/bin/activate

pip install -e .[dev]
```
To run the live auto-reload server:
```bash
uvicorn backend.app.main:app --reload --port 8000
```

### 3. Frontend Setup (React 18 + Vite + TypeScript)
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Running & Writing Tests

Before submitting any Pull Request, verify that all backend statistical unit and integration tests pass:
```bash
uv run pytest
```

When adding a new statistical method or modifying assumption thresholds:
1. Add tests in `backend/tests/` verifying accuracy against theoretical benchmarks or exact R outputs.
2. Ensure no `$p$-values` or statistical results are generated purely from LLM text prompts—**all math must run through verified Python (`scipy`/`statsmodels`) or R (`rpy2`/Jinja2 templates)**.

---

## 📥 Pull Request Guidelines

1. **Keep PRs Focused**: Address one feature, bug fix, or statistical method per pull request.
2. **Clear Description**: Explain the *what* and *why* of your change. If modifying statistical behavior, cite the mathematical reference or textbook benchmark.
3. **No Breaking Changes to Assumption Rules**: If adding or adjusting a diagnostic threshold (e.g., Levene's test alpha or Shapiro-Wilk sample limits), include rationale and backward compatibility notes.

---

## 🐞 Reporting Bugs & Suggesting Methods

If you find an edge case in our auto-type inference, assumption rules, or R script generation, please [open an issue](https://github.com/sujon-stat/quantigen-ai/issues) with:
- The dataset scale/structure (or sample synthetic CSV).
- The exact error or unexpected statistical output.
- Your expected benchmark output (e.g., SPSS or R `stats` output).

Thank you for helping us build trustworthy, assumption-verified statistical AI!
