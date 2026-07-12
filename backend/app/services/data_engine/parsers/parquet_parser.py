import pandas as pd
import io
import logging
from typing import List
from backend.app.services.data_engine.base import BaseDataParser, DataParserRegistry

logger = logging.getLogger(__name__)


@DataParserRegistry.register("parquet")
class ParquetParser(BaseDataParser):
    """
    Apache Parquet & Arrow Feather Parser (.parquet, .feather).
    High-performance binary columnar data parsing.
    """
    name: str = "Parquet / Feather Columnar Parser"
    supported_extensions: List[str] = [".parquet", ".feather", ".pq"]
    description: str = "High-performance columnar parser for Apache Parquet and Feather formats."

    def can_parse(self, filename: str, contents: bytes) -> bool:
        fn_lower = filename.lower()
        if any(fn_lower.endswith(ext) for ext in self.supported_extensions):
            return True
        # Parquet files begin and end with magic bytes PAR1
        return contents.startswith(b"PAR1") or contents.startswith(b"ARROW1")

    def parse(self, filename: str, contents: bytes, **kwargs) -> pd.DataFrame:
        buffer = io.BytesIO(contents)
        if filename.lower().endswith(".feather"):
            return pd.read_feather(buffer)
        return pd.read_parquet(buffer)
