import pandas as pd
import io
import logging
from typing import List
from backend.app.services.data_engine.base import BaseDataParser, DataParserRegistry

logger = logging.getLogger(__name__)


@DataParserRegistry.register("sas")
class SASParser(BaseDataParser):
    """
    SAS Data Parser (.sas7bdat, .xpt).
    Parses SAS binary datasets and transport files into tabular data.
    """
    name: str = "SAS Dataset Parser"
    supported_extensions: List[str] = [".sas7bdat", ".xpt"]
    description: str = "Parses SAS statistical datasets and XPORT transport files."

    def can_parse(self, filename: str, contents: bytes) -> bool:
        fn_lower = filename.lower()
        if any(fn_lower.endswith(ext) for ext in self.supported_extensions):
            return True
        # SAS7BDAT header signature or XPORT signature
        return contents.startswith(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc2\xea\x81\x60") or contents.startswith(b"HEADER RECORD**********")

    def parse(self, filename: str, contents: bytes, **kwargs) -> pd.DataFrame:
        buffer = io.BytesIO(contents)
        format_str = "xport" if filename.lower().endswith(".xpt") else "sas7bdat"
        try:
            df = pd.read_sas(buffer, format=format_str, encoding="latin-1")
            return df
        except Exception as e:
            try:
                import pyreadstat
                buffer.seek(0)
                if format_str == "xport":
                    df, _ = pyreadstat.read_xport(buffer)
                else:
                    df, _ = pyreadstat.read_sas7bdat(buffer)
                return df
            except Exception:
                raise ValueError(f"Failed to decode SAS dataset '{filename}': {e}")
