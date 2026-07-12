import pandas as pd
import io
import logging
from typing import List
from backend.app.services.data_engine.base import BaseDataParser, DataParserRegistry

logger = logging.getLogger(__name__)


@DataParserRegistry.register("csv")
class CSVParser(BaseDataParser):
    """
    Resilient CSV / TSV / TXT Data Parser.
    Handles multiple encodings (utf-8, latin-1, cp1252, iso-8859-1) and delimiter auto-detection.
    """
    name: str = "CSV / TSV Parser"
    supported_extensions: List[str] = [".csv", ".tsv", ".txt"]
    description: str = "Resilient multi-encoding parser for comma/tab separated text files."

    def can_parse(self, filename: str, contents: bytes) -> bool:
        fn_lower = filename.lower()
        if any(fn_lower.endswith(ext) for ext in self.supported_extensions):
            return True
        # Check if contents look like printable ASCII/UTF-8 text with delimiters
        try:
            sample = contents[:1024].decode("utf-8", errors="ignore")
            return "," in sample or "\t" in sample or ";" in sample
        except Exception:
            return False

    def parse(self, filename: str, contents: bytes, **kwargs) -> pd.DataFrame:
        sep = kwargs.get("sep", "\t" if filename.lower().endswith(".tsv") else None)
        encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
        
        for enc in encodings:
            try:
                buffer = io.BytesIO(contents)
                if sep is not None:
                    df = pd.read_csv(buffer, encoding=enc, sep=sep, on_bad_lines="skip")
                else:
                    df = pd.read_csv(buffer, encoding=enc, sep=None, engine="python", on_bad_lines="skip")
                
                # Perform basic numeric type coercion on ambiguous object columns
                for col in df.columns:
                    if df[col].dtype == object:
                        converted = pd.to_numeric(df[col], errors="coerce")
                        if len(df) > 0 and converted.notna().sum() > 0.3 * len(df):
                            df[col] = converted
                return df
            except Exception:
                continue

        raise ValueError(f"Failed to parse CSV/TSV '{filename}' across all supported encodings.")
