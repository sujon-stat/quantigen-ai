import pandas as pd
import io
import tempfile
import os
import logging
from typing import List
from backend.app.services.data_engine.base import BaseDataParser, DataParserRegistry

logger = logging.getLogger(__name__)


@DataParserRegistry.register("spss")
class SPSSParser(BaseDataParser):
    """
    SPSS Data Parser (.sav, .zsav).
    Extracts tabular data along with variable labels and value labels when pyreadstat/pandas is available.
    """
    name: str = "SPSS Dataset Parser (.sav)"
    supported_extensions: List[str] = [".sav", ".zsav"]
    description: str = "Parses IBM SPSS statistics data files, preserving column labels and categorical encodings."
    requires_external_lib: str = "pyreadstat"

    def can_parse(self, filename: str, contents: bytes) -> bool:
        fn_lower = filename.lower()
        if any(fn_lower.endswith(ext) for ext in self.supported_extensions):
            return True
        # Check SPSS magic header "$FL2"
        return contents.startswith(b"$FL2")

    def parse(self, filename: str, contents: bytes, **kwargs) -> pd.DataFrame:
        # pd.read_spss requires a file path or pyreadstat buffer
        try:
            import pyreadstat
            buffer = io.BytesIO(contents)
            df, meta = pyreadstat.read_sav(buffer, apply_value_formats=True)
            # Store labels in dataframe attrs if available
            if hasattr(meta, "column_labels") and meta.column_labels:
                df.attrs["variable_labels"] = dict(zip(df.columns, meta.column_labels))
            return df
        except ImportError:
            logger.warning("pyreadstat not installed. Attempting temporary file parse with pandas read_spss...")
            with tempfile.NamedTemporaryFile(suffix=".sav", delete=False) as tmp:
                tmp.write(contents)
                tmp_path = tmp.name
            try:
                df = pd.read_spss(tmp_path)
                return df
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
