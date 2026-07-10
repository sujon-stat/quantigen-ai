import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator
from backend.app.services.statistics.registry import MethodRegistry


class IntentRecommendation(BaseModel):
    method_id: str
    method_name: str
    confidence: float
    requires_confirmation: bool
    rationale: str
    mapped_variables: Dict[str, Any]
    suggested_variables: Optional[Dict[str, Any]] = None
    missing_variables: List[str] = []

    @model_validator(mode='after')
    def sync_variables(self) -> 'IntentRecommendation':
        if not self.suggested_variables and self.mapped_variables:
            self.suggested_variables = dict(self.mapped_variables)
        elif not self.mapped_variables and self.suggested_variables:
            self.mapped_variables = dict(self.suggested_variables)
        return self


class NaturalLanguageIntentParser:
    """Parses user queries against dataset metadata to recommend exact statistical methods and variable mappings."""

    @classmethod
    def parse_query(cls, query: str, columns_metadata: List[Dict[str, Any]]) -> IntentRecommendation:
        """
        Analyze user query string using keyword/heuristic matching and metadata column roles.
        `columns_metadata` format: [{"name": "salary", "type": "continuous"}, {"name": "gender", "type": "categorical"}]
        """
        q_lower = query.lower()
        safe_meta = []
        for col in (columns_metadata or []):
            if isinstance(col, dict):
                name = str(col.get("name") or col.get("id") or col.get("variable") or "")
                if name:
                    safe_meta.append({
                        "name": name,
                        "type": str(col.get("type") or col.get("inferred_type") or col.get("data_type") or "continuous"),
                        "n_unique": col.get("n_unique", col.get("unique_count", col.get("unique_values", 10)))
                    })
            elif isinstance(col, str) and col.strip():
                safe_meta.append({"name": col.strip(), "type": "continuous", "n_unique": 10})
        columns_metadata = safe_meta
        col_names = [col["name"] for col in columns_metadata]
        col_types = {col["name"]: col["type"] for col in columns_metadata}

        # 1. Detect column mentions in query
        mentioned_cols = []
        for col in col_names:
            # Check exact word boundary match or exact substring if column name > 2 chars
            if re.search(r'\b' + re.escape(col.lower()) + r'\b', q_lower) or (len(col) > 3 and col.lower() in q_lower):
                mentioned_cols.append(col)

        # 2. Match intent keywords
        is_diff = any(kw in q_lower for kw in ["differ", "difference", "compare", "higher", "lower", "between", "vs", "versus", "t-test", "ttest"])
        is_corr = any(kw in q_lower for kw in ["correlat", "associat", "relationship", "relation", "related", "pearson", "spearman"])
        is_reg = any(kw in q_lower for kw in ["predict", "depend on", "impact of", "effect of", "regression", "influence", "model"])
        is_freq = any(kw in q_lower for kw in ["proportio", "contingenc", "chi-square", "chisquare", "category", "distribut", "summary", "summarize", "describe"])
        is_anova = any(kw in q_lower for kw in ["anova", "one-way", "oneway", "f-test", "tukey", "three groups", "multiple groups", "several groups"])
        is_mw = any(kw in q_lower for kw in ["mann-whitney", "mann whitney", "wilcoxon", "u test", "rank sum", "nonparametric t-test"])
        is_logistic = any(kw in q_lower for kw in ["logistic", "odds ratio", "logit", "binary outcome", "classify", "probability of"])
        is_mult_reg = any(kw in q_lower for kw in ["multiple regression", "vif", "multiple linear", "several predictors", "multiple predictors"])
        is_unsupervised = any(kw in q_lower for kw in ["unsupervised", "cluster", "clustering", "k-means", "kmeans", "pca", "principal component", "dimensionality", "factor analysis", "dbscan", "hierarchical", "eigenvalue", "silhouette"])
        is_supervised = any(kw in q_lower for kw in ["supervised", "random forest", "xgboost", "gradient boost", "decision tree", "glm", "elastic net", "ridge", "lasso", "cross-validation", "train test", "train/test", "classification model", "predictive model"])

        cont_cols = [c for c in mentioned_cols if col_types.get(c) in ["continuous", "numeric", "float", "int", "count", "ordinal"]]
        cat_cols = [c for c in mentioned_cols if col_types.get(c) in ["categorical", "binary", "string", "object", "bool"]]
        bin_cols = [c for c in mentioned_cols if col_types.get(c) == "binary" or (next((col.get("n_unique", col.get("unique_count", 0)) for col in columns_metadata if col["name"] == c), 0) == 2)]

        # Check if query mentions exactly 2 continuous variables (or high-cardinality numeric columns)
        # For any two continuous variables where both have > 5 unique values, recommend Pearson Correlation or Linear Regression first!
        if len(mentioned_cols) == 2 and len(cont_cols) == 2:
            c1_meta = next((col for col in columns_metadata if col["name"] == cont_cols[0]), {})
            c2_meta = next((col for col in columns_metadata if col["name"] == cont_cols[1]), {})
            c1_levels = c1_meta.get("n_unique", c1_meta.get("unique_count", 100))
            c2_levels = c2_meta.get("n_unique", c2_meta.get("unique_count", 100))
            if c1_levels > 5 and c2_levels > 5 and not is_anova and not is_mw and not is_kw:
                conf = 0.95 if is_corr else 0.88
                return IntentRecommendation(
                    method_id="correlation_pearson",
                    method_name="Pearson Correlation",
                    confidence=conf,
                    requires_confirmation=(conf < 0.85),
                    rationale=f"You asked about the relationship or differences between '{cont_cols[0]}' and '{cont_cols[1]}'. Both are continuous numeric variables ({c1_levels} and {c2_levels} unique values), making Pearson Correlation the exact verified method.",
                    mapped_variables={"variables": [cont_cols[0], cont_cols[1]]},
                    missing_variables=[]
                )

        # Try Unsupervised Learning (PCA / K-Means Clustering / Dimensionality Reduction)
        if is_unsupervised:
            features = cont_cols if cont_cols else [col["name"] for col in columns_metadata if col.get("type") in ["continuous", "numeric", "float", "int", "count"]][:5]
            if not features and columns_metadata:
                features = [col["name"] for col in columns_metadata][:4]
            method_name = "Principal Component Analysis (PCA)" if any(kw in q_lower for kw in ["pca", "principal component", "dimensionality", "factor"]) else "K-Means Clustering"
            method_id = "pca_reduction" if "PCA" in method_name else "kmeans_clustering"
            return IntentRecommendation(
                method_id=method_id,
                method_name=method_name,
                confidence=0.94,
                requires_confirmation=False,
                rationale=f"You asked to perform unsupervised learning ({method_name}) across numeric features ('{', '.join(features)}').",
                mapped_variables={"features": features},
                missing_variables=[]
            )

        # Try Supervised Learning (Random Forest / GLM / Advanced Ensemble)
        if is_supervised:
            target = bin_cols[0] if bin_cols else (cont_cols[0] if cont_cols else (columns_metadata[0]["name"] if columns_metadata else "target"))
            preds = [c for c in mentioned_cols if c != target]
            if not preds and columns_metadata:
                preds = [col["name"] for col in columns_metadata if col["name"] != target][:4]
            method_name = "Random Forest Ensemble" if any(kw in q_lower for kw in ["random forest", "xgboost", "tree", "ensemble", "gradient"]) else "Generalized Linear Model (GLM)"
            method_id = "random_forest" if "Random Forest" in method_name else "glm_regression"
            return IntentRecommendation(
                method_id=method_id,
                method_name=method_name,
                confidence=0.94,
                requires_confirmation=False,
                rationale=f"You asked to build a supervised predictive model ({method_name}) targeting '{target}' from predictors ('{', '.join(preds)}').",
                mapped_variables={"dependent": target, "independent": preds},
                missing_variables=[]
            )

        # Try Logistic Regression first if explicit keyword or binary outcome prediction
        if is_logistic or (is_reg and bin_cols and len(cont_cols + cat_cols) >= 2):
            dep = bin_cols[0] if bin_cols else (cat_cols[0] if cat_cols else None)
            if not dep and is_logistic and columns_metadata:
                dep = next((col["name"] for col in columns_metadata if col.get("type") in ["binary", "categorical", "bool"] or col.get("n_unique", 999) <= 10), columns_metadata[0]["name"])
            if dep or is_logistic:
                if not dep and columns_metadata:
                    dep = columns_metadata[0]["name"]
                preds = [c for c in mentioned_cols if c != dep]
                if not preds and columns_metadata:
                    preds = [col["name"] for col in columns_metadata if col["name"] != dep and col.get("type") in ["continuous", "numeric", "float", "int", "count", "categorical", "binary", "string", "ordinal"]][:3]
                if preds or is_logistic:
                    conf = 0.94 if is_logistic else 0.85
                    return IntentRecommendation(
                        method_id="regression_logistic",
                        method_name="Binary Logistic Regression",
                        confidence=conf,
                        requires_confirmation=(conf < 0.85),
                        rationale=f"You asked to model or predict a binary outcome ('{dep}') from predictor variables ('{', '.join(preds)}').",
                        mapped_variables={"dependent": dep, "independent": preds},
                        missing_variables=[]
                    )

        # Try Multiple Linear Regression
        if is_mult_reg or (is_reg and len(cont_cols) >= 3):
            dep = cont_cols[0]
            preds = cont_cols[1:]
            if "predict" in q_lower:
                parts = re.split(r'\b(?:from|using|with|by)\b', q_lower)
                if len(parts) == 2:
                    for c in cont_cols:
                        if c.lower() in parts[0]:
                            dep = c
                            preds = [p for p in cont_cols if p != dep]
                            break
            conf = 0.93 if is_mult_reg else 0.85
            return IntentRecommendation(
                method_id="regression_linear_multiple",
                method_name="Multiple Linear Regression",
                confidence=conf,
                requires_confirmation=(conf < 0.85),
                rationale=f"You asked to predict continuous outcome '{dep}' from multiple predictors ('{', '.join(preds)}').",
                mapped_variables={"dependent": dep, "independent": preds},
                missing_variables=[]
            )

        # Try Kruskal-Wallis
        if is_kw:
            dep = cont_cols[0] if cont_cols else next((c for c, t in col_types.items() if t in ["continuous", "numeric", "float", "int", "count", "ordinal"]), None)
            grp = cat_cols[0] if cat_cols else next((c for c, t in col_types.items() if t in ["categorical", "string", "object"]), None)
            if dep and grp:
                return IntentRecommendation(
                    method_id="kruskal_wallis",
                    method_name="Kruskal-Wallis H Test",
                    confidence=0.94,
                    requires_confirmation=False,
                    rationale=f"You asked to conduct a Kruskal-Wallis non-parametric comparison of '{dep}' across groups of '{grp}'.",
                    mapped_variables={"dependent": dep, "grouping": grp},
                    missing_variables=[]
                )

        # Try Mann-Whitney U
        if is_mw:
            dep = cont_cols[0] if cont_cols else next((c for c, t in col_types.items() if t in ["continuous", "numeric", "float", "int", "count", "ordinal"]), None)
            grp = cat_cols[0] if cat_cols else next((c for c, t in col_types.items() if t in ["categorical", "binary", "string", "object", "bool"]), None)
            if dep and grp:
                return IntentRecommendation(
                    method_id="mann_whitney_u",
                    method_name="Mann-Whitney U Test",
                    confidence=0.94,
                    requires_confirmation=False,
                    rationale=f"You asked to conduct a Mann-Whitney U non-parametric comparison of '{dep}' across two groups of '{grp}'.",
                    mapped_variables={"dependent": dep, "grouping": grp},
                    missing_variables=[]
                )

        # Try One-Way ANOVA
        if is_anova:
            dep = cont_cols[0] if cont_cols else next((c for c, t in col_types.items() if t in ["continuous", "numeric", "float", "int", "count"]), None)
            grp = cat_cols[0] if cat_cols else next((c for c, t in col_types.items() if t in ["categorical", "string", "object"]), None)
            if dep and grp:
                return IntentRecommendation(
                    method_id="anova_oneway",
                    method_name="One-Way ANOVA",
                    confidence=0.94,
                    requires_confirmation=False,
                    rationale=f"You asked to compare means of '{dep}' across multiple groups of '{grp}' using One-Way ANOVA.",
                    mapped_variables={"dependent": dep, "grouping": grp},
                    missing_variables=[]
                )

        # 3. Method evaluation (Phase 0 logic with enhanced grouping check)
        # Try T-Test vs ANOVA based on group count metadata if both compare
        if is_diff or (len(mentioned_cols) == 2 and set([col_types.get(c) for c in mentioned_cols]) <= {"continuous", "numeric", "float", "int", "count", "categorical", "binary", "string", "object", "bool"} and len(cont_cols) == 1):
            dep = cont_cols[0] if cont_cols else next((c for c, t in col_types.items() if t in ["continuous", "numeric", "float", "int", "count"]), None)
            grp = cat_cols[0] if cat_cols else next((c for c, t in col_types.items() if t in ["categorical", "binary", "string", "object", "bool"]), None)
            if dep and grp:
                # Check if metadata specifies 3+ groups for categorical variable
                grp_meta = next((col for col in columns_metadata if col["name"] == grp), {})
                grp_levels = grp_meta.get("n_unique", grp_meta.get("unique_count", 2))
                
                # If grouping variable has > 15 unique values (high cardinality / continuous), redirect to Pearson Correlation
                if grp_levels > 15:
                    return IntentRecommendation(
                        method_id="correlation_pearson",
                        method_name="Pearson Correlation",
                        confidence=0.92,
                        requires_confirmation=False,
                        rationale=f"Both '{dep}' and '{grp}' have many distinct values ({grp_levels} values for '{grp}'). For continuous/high-cardinality relationships, Pearson Correlation is the exact verified method.",
                        mapped_variables={"variables": [dep, grp]},
                        missing_variables=[]
                    )
                elif grp_levels >= 3:
                    conf = 0.90 if is_diff else 0.78
                    return IntentRecommendation(
                        method_id="anova_oneway",
                        method_name="One-Way ANOVA",
                        confidence=conf,
                        requires_confirmation=(conf < 0.85),
                        rationale=f"You asked to compare differences across groups. '{dep}' is continuous and '{grp}' has {grp_levels} categories, which requires One-Way ANOVA.",
                        mapped_variables={"dependent": dep, "grouping": grp},
                        missing_variables=[]
                    )
                else:
                    conf = 0.92 if (dep in mentioned_cols and grp in mentioned_cols and is_diff) else 0.75
                    return IntentRecommendation(
                        method_id="ttest_independent",
                        method_name="Independent Samples T-Test",
                        confidence=conf,
                        requires_confirmation=(conf < 0.85),
                        rationale=f"You asked to compare differences across groups. '{dep}' is a continuous outcome and '{grp}' is a binary/two-group categorical variable.",
                        mapped_variables={"dependent": dep, "grouping": grp},
                        missing_variables=[]
                    )

        # Try Simple Linear Regression
        if is_reg or (is_diff and len(mentioned_cols) == 2 and all(col_types.get(c) in ["continuous", "numeric", "float", "int", "count"] for c in mentioned_cols)):
            if len(cont_cols) >= 2:
                dep, ind = cont_cols[0], cont_cols[1]
                if "predict" in q_lower:
                    parts = re.split(r'\b(?:from|using|with|by)\b', q_lower)
                    if len(parts) == 2:
                        for c in cont_cols:
                            if c.lower() in parts[0]:
                                dep = c
                            elif c.lower() in parts[1]:
                                ind = c
                conf = 0.90 if is_reg else 0.78
                return IntentRecommendation(
                    method_id="regression_linear_simple",
                    method_name="Simple Linear Regression",
                    confidence=conf,
                    requires_confirmation=(conf < 0.85),
                    rationale=f"You asked to model or predict an outcome from a predictor. Both '{dep}' (Y) and '{ind}' (X) are continuous variables.",
                    mapped_variables={"dependent": dep, "independent": ind},
                    missing_variables=[]
                )

        # Try Pearson Correlation
        if is_corr or (len(mentioned_cols) == 2 and all(col_types.get(c) in ["continuous", "numeric", "float", "int", "count"] for c in mentioned_cols)):
            if len(cont_cols) >= 2:
                conf = 0.93 if is_corr else 0.80
                return IntentRecommendation(
                    method_id="correlation_pearson",
                    method_name="Pearson Correlation",
                    confidence=conf,
                    requires_confirmation=(conf < 0.85),
                    rationale=f"You asked to evaluate the relationship/association between two continuous numeric variables ('{cont_cols[0]}' and '{cont_cols[1]}').",
                    mapped_variables={"variables": [cont_cols[0], cont_cols[1]]},
                    missing_variables=[]
                )

        # Try Chi-Square
        if is_freq or (len(mentioned_cols) == 2 and all(col_types.get(c) in ["categorical", "binary", "string", "object", "bool"] for c in mentioned_cols)):
            if len(cat_cols) >= 2:
                conf = 0.91 if is_freq else 0.82
                return IntentRecommendation(
                    method_id="chi_square_independence",
                    method_name="Chi-Square Test of Independence",
                    confidence=conf,
                    requires_confirmation=(conf < 0.85),
                    rationale=f"You asked to test the association or contingency between two categorical variables ('{cat_cols[0]}' and '{cat_cols[1]}').",
                    mapped_variables={"variables": [cat_cols[0], cat_cols[1]]},
                    missing_variables=[]
                )

        # Default fallback: Descriptive Statistics
        target_cols = mentioned_cols if mentioned_cols else col_names[:5]
        return IntentRecommendation(
            method_id="descriptive_stats",
            method_name="Descriptive Statistics",
            confidence=0.70 if not mentioned_cols else 0.85,
            requires_confirmation=True,
            rationale="No specific hypothesis testing intent detected; recommending comprehensive descriptive summary profiling of your selected or primary dataset variables.",
            mapped_variables={"variables": target_cols},
            missing_variables=[]
        )
