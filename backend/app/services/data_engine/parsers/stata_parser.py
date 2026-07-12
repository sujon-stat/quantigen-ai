import pandas as pd
import io
import logging
from typing import List
from backend.app.services.data_engine.base import BaseDataParser, DataParserRegistry

logger = logging.getLogger(__name__)


@DataParserRegistry.register("stata")
class StataParser(BaseDataParser):
    """
    Stata Data Parser (.dta).
    Parses Stata dataset files across formats (dta 113 to 119+).
    """
    name: str = "Stata Dataset Parser (.dta)"
    supported_extensions: List[str] = [".dta"]
    description: str = "Parses Stata datasets, preserving variable and value labels."

    def can_parse(self, filename: str, contents: bytes) -> bool:
        fn_lower = filename.lower()
        if fn_lower.endswith(".dta"):
            return True
        # Check Stata magic header (<stata_dta>)
        return contents.startswith(b"<stata_dta>") or contents[:4] in [b"\x6f\x01", b"\x70\x01", b"\x71\x01", b"\x72\x01", b"\x75\x01"]

    def parse(self, filename: str, contents: bytes, **kwargs) -> pd.DataFrame:
        buffer = io.BytesIO(contents)
        try:
            df = pd.read_stata(buffer)
            return df
        except Exception as e:
            try:
                import pyreadstat
                buffer.seek(0)
                df, meta = pyreadstat.read_dta(buffer, apply_value_formats=True)
                if hasattr(meta, "column_labels") and meta.column_labels:
                    df.attrs["variable_labels"] = dict(zip(df.columns, meta.column_labels))
                return df
            except Exception:
                raise ValueError(f"Failed to decode Stata dataset '{filename}': {e}")
