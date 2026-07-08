import io
import uuid
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body
from pydantic import BaseModel
from backend.app.models.dataset import DatasetSummary, ColumnProfile
from backend.app.models.variables import VariableType
from backend.app.services.session.manager import session_manager
from backend.app.core.exceptions import StatMindException, StatMindErrorLevel

router = APIRouter()


class VariableUpdate(BaseModel):
    detected_type: VariableType


class DatasetCleanOptions(BaseModel):
    drop_duplicates: bool = False
    dropna_cols: Optional[List[str]] = None


def detect_column_profile(series: pd.Series, name: str) -> ColumnProfile:
    """Analyze a single pandas column to determine its statistical properties and VariableType."""
    n_total = len(series)
    n_missing = int(series.isna().sum())
    missing_pct = round((n_missing / n_total) * 100, 2) if n_total > 0 else 0.0
    
    clean_series = series.dropna()
    unique_vals = int(clean_series.nunique())
    sample_vals = clean_series.head(5).tolist()
    
    # Auto-detect VariableType
    detected_type = VariableType.CATEGORICAL
    if pd.api.types.is_datetime64_any_dtype(clean_series):
        detected_type = VariableType.DATETIME
    elif pd.api.types.is_bool_dtype(clean_series) or (unique_vals == 2 and set(clean_series.unique()) <= {0, 1, True, False, "Yes", "No", "M", "F", 0.0, 1.0}):
        detected_type = VariableType.BINARY
    elif pd.api.types.is_numeric_dtype(clean_series):
        if unique_vals <= 5:
            # Small discrete integer scale likely ordinal/categorical
            detected_type = VariableType.ORDINAL
        elif pd.api.types.is_integer_dtype(clean_series) and (clean_series >= 0).all() and unique_vals < 15 and clean_series.max() < 50:
            detected_type = VariableType.COUNT
        else:
            detected_type = VariableType.CONTINUOUS
    elif unique_vals == n_total and n_total > 10:
        # High cardinality unique text is likely ID column
        detected_type = VariableType.CATEGORICAL
        
    summary_stats: Dict[str, Any] = {}
    if detected_type in [VariableType.CONTINUOUS, VariableType.COUNT]:
        summary_stats = {
            "mean": round(float(clean_series.mean()), 4) if len(clean_series) > 0 else None,
            "std": round(float(clean_series.std()), 4) if len(clean_series) > 1 else None,
            "min": float(clean_series.min()) if len(clean_series) > 0 else None,
            "max": float(clean_series.max()) if len(clean_series) > 0 else None,
            "median": float(clean_series.median()) if len(clean_series) > 0 else None,
            "q25": float(clean_series.quantile(0.25)) if len(clean_series) > 0 else None,
            "q75": float(clean_series.quantile(0.75)) if len(clean_series) > 0 else None,
        }
    else:
        # Categorical top counts
        val_counts = clean_series.value_counts().head(5)
        summary_stats = {
            "top_categories": {str(k): int(v) for k, v in val_counts.items()}
        }

    return ColumnProfile(
        name=name,
        detected_type=detected_type,
        missing_count=n_missing,
        missing_percentage=missing_pct,
        unique_values=unique_vals,
        sample_values=[str(v) if isinstance(v, (pd.Timestamp, np.generic)) else v for v in sample_vals],
        summary_stats=summary_stats
    )


def profile_dataframe(df: pd.DataFrame, dataset_name: str, dataset_id: Optional[str] = None) -> DatasetSummary:
    """Generate a complete DatasetSummary metadata profile from a pandas DataFrame."""
    ds_id = dataset_id or str(uuid.uuid4())
    n_rows, n_cols = df.shape
    
    if n_rows == 0:
        raise StatMindException(error_code="EmptyDataError", level=StatMindErrorLevel.USER_ERROR)
        
    variables = [detect_column_profile(df[col], str(col)) for col in df.columns]
    
    total_missing = sum(v.missing_count for v in variables)
    cols_with_missing = sum(1 for v in variables if v.missing_count > 0)
    
    if total_missing == 0:
        missing_summary = "Complete dataset with no missing values (100% complete)."
    else:
        missing_summary = f"{total_missing} missing values across {cols_with_missing} columns ({round((total_missing/(n_rows*n_cols))*100, 1)}% of all cells)."
        
    preview_records = df.head(10).replace({np.nan: None}).to_dict(orient="records")
    return DatasetSummary(
        dataset_id=ds_id,
        name=dataset_name,
        n_rows=n_rows,
        n_columns=n_cols,
        variables=variables,
        preview_data=preview_records,
        missing_summary=missing_summary
    )


def _parse_csv_resilient(contents: bytes) -> pd.DataFrame:
    """Parse CSV with resilience for metadata preambles, encoding issues, trailing commas, and custom missing indicators."""
    # Strategy 1: Standard parse with utf-8-sig / latin1 (for clean CSVs)
    for encoding in ["utf-8-sig", "utf-8", "latin1"]:
        try:
            df = pd.read_csv(io.BytesIO(contents), encoding=encoding)
            if len(df.columns) >= 2 and df.shape[0] > 0 and df.iloc[:, 0].notna().mean() > 0.5:
                df = df.dropna(axis=1, how="all")
                return df
        except Exception:
            pass

    # Strategy 2: Pre-filter tabular lines, strip trailing commas, and auto-clean metadata headers
    text = contents.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()

    comma_counts = [line.count(",") for line in lines if line.strip()]
    if not comma_counts:
        raise ValueError("File appears empty or contains no CSV structure.")
    
    from collections import Counter
    valid_counts = [c for c in comma_counts if c >= 2]
    if not valid_counts:
        raise ValueError("File does not contain tabular CSV data (not enough columns).")
    
    most_common_comma_count = Counter(valid_counts).most_common(1)[0][0]
    
    tabular_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        c = stripped.count(",")
        if abs(c - most_common_comma_count) <= 2:
            while stripped.endswith(","):
                stripped = stripped[:-1]
            tabular_lines.append(stripped)

    if not tabular_lines:
        raise ValueError("Could not extract tabular lines from CSV.")

    cleaned_csv_text = "\n".join(tabular_lines)
    for sep in [",", ";", "\t"]:
        try:
            df = pd.read_csv(io.StringIO(cleaned_csv_text), sep=sep, index_col=False, on_bad_lines="skip", dtype=str)
            if len(df.columns) >= 2 and df.shape[0] > 0:
                df = df.dropna(axis=1, how="all")
                df = df.loc[:, ~df.columns.str.contains('^Unnamed') | df.notna().any()]
                df.columns = [str(col).strip() for col in df.columns]
                
                # Remove repeated headers across multi-year/multi-station data
                first_col = df.columns[0]
                df = df[df[first_col] != first_col]
                
                # Remove non-tabular metadata lines (e.g., station banners)
                df = df[~df[first_col].astype(str).str.lower().str.startswith(("station", "bangladesh", "daily"))]
                df = df.reset_index(drop=True)
                
                # Convert numeric columns safely (handling markers like '****' as NaN)
                for col in df.columns:
                    converted = pd.to_numeric(df[col], errors="coerce")
                    if len(df) > 0 and converted.notna().sum() > 0.3 * len(df):
                        df[col] = converted
                        
                return df
        except Exception:
            continue

    raise ValueError("Could not parse CSV with any strategy. Please ensure the file is a valid CSV.")


@router.post("/upload", response_model=DatasetSummary, status_code=201)
async def upload_dataset(file: UploadFile = File(...)):
    """Upload and profile a dataset (CSV, XLSX, TSV, JSON)."""
    filename = file.filename or "uploaded_dataset.csv"
    contents = await file.read()
    
    try:
        filename_lower = filename.lower()
        if filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(contents))
        elif filename_lower.endswith(".tsv"):
            df = pd.read_csv(io.BytesIO(contents), sep="\t")
        elif filename_lower.endswith(".json"):
            df = pd.read_json(io.BytesIO(contents))
        else:
            df = _parse_csv_resilient(contents)
    except Exception as e:
        raise StatMindException(
            error_code="ParserError",
            level=StatMindErrorLevel.USER_ERROR,
            raw_error=e
        )
        
    profile = profile_dataframe(df, dataset_name=filename)
    session_manager.save_dataset(profile, df)
    return profile


@router.get("/{dataset_id}", status_code=200)
async def get_dataset_details(dataset_id: str, limit: int = Query(20, ge=1, le=100)):
    """Retrieve dataset summary and a preview of rows."""
    profile, df = session_manager.get_dataset(dataset_id)
    preview_records = df.head(limit).replace({np.nan: None}).to_dict(orient="records")
    return {
        "profile": profile.model_dump(),
        "preview_rows": preview_records
    }


@router.patch("/{dataset_id}/variables/{variable_name}", response_model=DatasetSummary, status_code=200)
async def update_variable(dataset_id: str, variable_name: str, update: VariableUpdate):
    """Update the detected VariableType of a specific dataset column."""
    updated_profile = session_manager.update_variable_type(
        dataset_id=dataset_id,
        var_name=variable_name,
        new_type=update.detected_type
    )
    return updated_profile


@router.post("/{dataset_id}/clean", response_model=DatasetSummary, status_code=200)
async def clean_dataset(dataset_id: str, options: DatasetCleanOptions):
    """Perform automated data cleaning on an uploaded dataset."""
    updated_profile = session_manager.clean_dataset(
        dataset_id=dataset_id,
        drop_duplicates=options.drop_duplicates,
        dropna_cols=options.dropna_cols
    )
    return updated_profile
