import pandas as pd
import io
import logging
from typing import List
from backend.app.services.data_engine.base import BaseDataParser, DataParserRegistry

logger = logging.getLogger(__name__)


@DataParserRegistry.register("excel")
class ExcelParser(BaseDataParser):
    """
    Excel Data Parser (.xlsx, .xls, .xlsm, .xlsb).
    Extracts sheets and recovers clean tabular structures.
    """
    name: str = "Excel Workbook Parser"
    supported_extensions: List[str] = [".xlsx", ".xls", ".xlsm", ".xlsb"]
    description: str = "Parses Microsoft Excel workbooks into tabular data structures."

    def can_parse(self, filename: str, contents: bytes) -> bool:
        fn_lower = filename.lower()
        if any(fn_lower.endswith(ext) for ext in self.supported_extensions):
            return True
        # Check PK zip magic header (50 4B 03 04) for xlsx or OLE2 header for xls
        return contents.startswith(b"PK\x03\x04") or contents.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")

    def parse(self, filename: str, contents: bytes, **kwargs) -> pd.DataFrame:
        buffer = io.BytesIO(contents)
        sheet_name = kwargs.get("sheet_name", 0)
        df = pd.read_excel(buffer, sheet_name=sheet_name)
        return df
