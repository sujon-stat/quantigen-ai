import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
from backend.app.models.analysis import MethodResult
from backend.app.services.statistics.base import BaseStatisticalMethod
from backend.app.services.r_integration.code_gen import CodeGenerator
from backend.app.services.visualization.themes import STATMIND_THEME, apply_statmind_theme, format_ai_label
import plotly.graph_objects as go
import json


class DescriptiveStatisticsMethod(BaseStatisticalMethod):
    method_id = "descriptive_stats"
    method_name = "Descriptive Statistics"
    method_family = "Summary & Exploratory"
    description = "Computes comprehensive summary statistics, distribution shape (skewness, kurtosis), and missing value diagnostics across numeric and categorical variables."
    required_variables = {"variables": ["continuous", "categorical"]}
    optional_variables = {}

    def run(self, data: pd.DataFrame, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> MethodResult:
        errors = self.validate_variables(data, variables)
        if errors:
            raise ValueError(f"Variable validation failed: {', '.join(errors)}")

        var_list = variables["variables"]
        if isinstance(var_list, str):
            var_list = [var_list]

        df_subset = data[var_list]
        n_rows = len(df_subset)

        # Run assumption checks (empty for descriptive)
        assumptions = self.check_assumptions(data, variables)

        main_results = {
            "numeric_summaries": {},
            "categorical_summaries": {}
        }

        for col in var_list:
            s = df_subset[col]
            missing_cnt = int(s.isna().sum())
            missing_pct = float(missing_cnt / n_rows * 100) if n_rows > 0 else 0.0

            if pd.api.types.is_numeric_dtype(s):
                clean_s = s.dropna()
                if not clean_s.empty:
                    q25, median_val, q75 = np.percentile(clean_s, [25, 50, 75])
                    main_results["numeric_summaries"][col] = {
                        "count": int(clean_s.count()),
                        "mean": float(clean_s.mean()),
                        "std": float(clean_s.std()),
                        "median": float(median_val),
                        "iqr": float(q75 - q25),
                        "min": float(clean_s.min()),
                        "max": float(clean_s.max()),
                        "skewness": float(clean_s.skew()),
                        "kurtosis": float(clean_s.kurtosis()),
                        "missing_count": missing_cnt,
                        "missing_percentage": missing_pct
                    }
            else:
                clean_s = s.dropna().astype(str)
                val_counts = clean_s.value_counts()
                top_cat = str(val_counts.index[0]) if not val_counts.empty else "None"
                top_cnt = int(val_counts.iloc[0]) if not val_counts.empty else 0
                main_results["categorical_summaries"][col] = {
                    "count": int(clean_s.count()),
                    "unique_categories": int(clean_s.nunique()),
                    "top_category": top_cat,
                    "top_frequency": top_cnt,
                    "frequencies": val_counts.head(10).to_dict(),
                    "missing_count": missing_cnt,
                    "missing_percentage": missing_pct
                }

        r_code = self.generate_r_code(variables, options)
        py_code = self._generate_python_code(var_list)
        plots = self.generate_plots(df_subset, variables, main_results)
        interpretation = self.interpret(main_results, variables)

        return MethodResult(
            method_id=self.method_id,
            method_name=self.method_name,
            method_family=self.method_family,
            description=self.description,
            variables_used=variables,
            sample_size=n_rows,
            assumption_results=assumptions,
            main_results=main_results,
            effect_sizes=None,
            post_hoc_results=None,
            python_code=py_code,
            r_code=r_code,
            plots=plots,
            interpretation=interpretation,
            warnings=[],
            references=["Wickham, H. & Grolemund, G. (2016). R for Data Science."]
        )

    def generate_r_code(self, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> str:
        return CodeGenerator.render_r_template("descriptive.R.j2", {"variables": variables.get("variables", [])})

    def _generate_python_code(self, var_list: List[str]) -> str:
        code = f"""import pandas as pd
import scipy.stats as stats

# Select variables
vars_to_analyze = {var_list}
subset = data[vars_to_analyze]

# Numeric summary
numeric_cols = subset.select_dtypes(include='number').columns
if len(numeric_cols) > 0:
    print("Numeric Summary:")
    print(subset[numeric_cols].describe().T)
    for c in numeric_cols:
        print(f"{{c}} Skewness: {{subset[c].skew():.3f}}, Kurtosis: {{subset[c].kurtosis():.3f}}")

# Categorical summary
cat_cols = subset.select_dtypes(exclude='number').columns
for c in cat_cols:
    print(f"\\nCategorical Summary for {{c}}:")
    print(subset[c].value_counts(dropna=False))
"""
        return CodeGenerator.format_python_code("Descriptive Statistics", code)

    def generate_plots(self, data: pd.DataFrame, variables: Dict[str, Any], results: Dict[str, Any]) -> List[Dict[str, Any]]:
        plots = []
        var_list = variables["variables"]
        if isinstance(var_list, str):
            var_list = [var_list]

        # Prioritize continuous/numeric variables first so the top 3 displayed in UI are continuous measurements
        num_cols = [col for col in var_list if col in results.get("numeric_summaries", {})]
        cat_cols = [col for col in var_list if col in results.get("categorical_summaries", {})]
        ordered_cols = (num_cols + cat_cols)[:20]  # Return up to 20 prioritized plots for progressive disclosure

        for i, col in enumerate(ordered_cols):
            if col in results.get("numeric_summaries", {}):
                num_s = results["numeric_summaries"][col]
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=data[col].dropna(),
                    name=format_ai_label(col),
                    marker_color=STATMIND_THEME["categorical_palette"][i % len(STATMIND_THEME["categorical_palette"])],
                    opacity=0.8
                ))
                fig.update_xaxes(title_text=f"{format_ai_label(col)} (Continuous Measurement)")
                fig.update_yaxes(title_text="Observation Frequency (n)")
                ai_title = f"Population Distribution of {format_ai_label(col)}"
                ai_sub = f"Sample Mean: {num_s.get('mean', 0):.2f} | Std Dev: {num_s.get('std', 0):.2f} | Median: {num_s.get('median', 0):.2f} (n = {num_s.get('count', 0):,})"
                fig = apply_statmind_theme(fig, title=ai_title, subtitle=ai_sub)
                plots.append(json.loads(fig.to_json()))
            elif col in results.get("categorical_summaries", {}):
                cat_s = results["categorical_summaries"][col]
                freqs = cat_s["frequencies"]
                fig = go.Figure(go.Bar(
                    x=list(freqs.keys()),
                    y=list(freqs.values()),
                    name=format_ai_label(col),
                    marker_color=STATMIND_THEME["categorical_palette"][i % len(STATMIND_THEME["categorical_palette"])]
                ))
                fig.update_xaxes(title_text=f"{format_ai_label(col)} (Category / Level)")
                fig.update_yaxes(title_text="Total Count (Observations)")
                ai_title = f"Demographic & Categorical Frequency of {format_ai_label(col)}"
                top_c = cat_s.get("top_category", "N/A")
                top_f = cat_s.get("top_frequency", 0)
                tot_n = cat_s.get("count", 1)
                pct = (top_f / tot_n * 100) if tot_n > 0 else 0
                ai_sub = f"Total Unique Categories: {cat_s.get('unique_categories', 0):,} | Most Frequent: '{top_c}' ({top_f:,} obs, {pct:.1f}%)"
                fig = apply_statmind_theme(fig, title=ai_title, subtitle=ai_sub)
                plots.append(json.loads(fig.to_json()))
        return plots

    def interpret(self, results: Dict[str, Any], variables: Dict[str, Any]) -> str:
        num_summaries = results.get("numeric_summaries", {})
        cat_summaries = results.get("categorical_summaries", {})
        total_vars = len(num_summaries) + len(cat_summaries)
        lines = ["**Descriptive Analysis Summary:**"]
        
        # Display top 10 most informative variables in narrative to prevent firehose overload
        displayed_count = 0
        for col, s in num_summaries.items():
            if displayed_count >= 10:
                break
            skew_desc = "approximately symmetric" if abs(s["skewness"]) < 0.5 else ("moderately skewed" if abs(s["skewness"]) < 1.0 else "highly skewed")
            lines.append(f"- **{col}** (n = {s['count']:,}): Mean = {s['mean']:.2f} (SD = {s['std']:.2f}), Median = {s['median']:.2f}. Distribution is {skew_desc} (Skewness = {s['skewness']:.2f}).")
            if s["missing_count"] > 0:
                lines.append(f"  - *Missing observations*: {s['missing_count']} ({s['missing_percentage']:.1f}%)")
            displayed_count += 1

        for col, s in cat_summaries.items():
            if displayed_count >= 10:
                break
            lines.append(f"- **{col}** (n = {s['count']:,}): {s['unique_categories']:,} distinct categories. Most frequent level is **'{s['top_category']}'** with {s['top_frequency']:,} occurrences ({s['top_frequency']/s['count']*100:.1f}%).")
            displayed_count += 1
            
        if total_vars > 10:
            lines.append(f"\n*(Progressive Disclosure: Top 10 of {total_vars} variables summarized above. Complete metrics for every variable are tabulated cleanly in the Q1 Journal Table above and available in the export portfolio.)*")
            
        return "\n".join(lines)
