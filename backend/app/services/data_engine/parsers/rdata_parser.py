import pandas as pd
import io
import tempfile
import os
import logging
from typing import List
from backend.app.services.data_engine.base import BaseDataParser, DataParserRegistry

logger = logging.getLogger(__name__)


@DataParserRegistry.register("rdata")
class RDataParser(BaseDataParser):
    """
    R Statistical Data Archive Parser (.rdata, .rda, .rds).
    Extracts dataframes from R serialization objects using pyreadr or our R Engine bridge.
    """
    name: str = "R Data Archive Parser (.RData / .RDS)"
    supported_extensions: List[str] = [".rdata", ".rda", ".rds"]
    description: str = "Parses R object serialized archives, extracting native R dataframes into Python."
    requires_external_lib: str = "pyreadr"

    def can_parse(self, filename: str, contents: bytes) -> bool:
        fn_lower = filename.lower()
        if any(fn_lower.endswith(ext) for ext in self.supported_extensions):
            return True
        # Gzip or R serialization header checks
        return contents.startswith(b"\x1f\x8b\x08") or contents.startswith(b"RDX2") or contents.startswith(b"RDA2")

    def parse(self, filename: str, contents: bytes, **kwargs) -> pd.DataFrame:
        try:
            import pyreadr
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False) as tmp:
                tmp.write(contents)
                tmp_path = tmp.name
            try:
                if filename.lower().endswith(".rds"):
                    res = pyreadr.read_r(tmp_path)
                    # RDS typically returns None key or object name
                    for k, df in res.items():
                        if isinstance(df, pd.DataFrame):
                            return df
                else:
                    res = pyreadr.read_r(tmp_path)
                    for k, df in res.items():
                        if isinstance(df, pd.DataFrame):
                            return df
                raise ValueError("No tabular DataFrame found inside R archive.")
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except ImportError:
            logger.warning("pyreadr not available. Attempting R Engine (rpy2) bridge extraction...")
            # Fallback to rpy2 if available
            try:
                import rpy2.robjects as ro
                from rpy2.robjects import pandas2ri
                pandas2ri.activate()
                with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False) as tmp:
                    tmp.write(contents)
                    tmp_path = tmp.name
                try:
                    if filename.lower().endswith(".rds"):
                        r_obj = ro.r["readRDS"](tmp_path)
                        return ro.conversion.rpy2py(r_obj)
                    else:
                        loaded_names = ro.r["load"](tmp_path)
                        for name in loaded_names:
                            obj = ro.globalenv[name]
                            if "data.frame" in obj.rclass:
                                return ro.conversion.rpy2py(obj)
                    raise ValueError("Could not extract data.frame from R object.")
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            except Exception as e:
                raise ValueError(f"Failed to parse R data archive '{filename}': {e}. Please install 'pyreadr' or 'rpy2'.")
