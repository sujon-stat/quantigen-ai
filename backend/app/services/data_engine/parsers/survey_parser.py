import pandas as pd
import io
import json
import logging
from typing import List
from backend.app.services.data_engine.base import BaseDataParser, DataParserRegistry

logger = logging.getLogger(__name__)


@DataParserRegistry.register("survey")
class SurveyArchiveParser(BaseDataParser):
    """
    Epidemiological & Global Survey Export Parser (.redcap, .kobo, .dhs, .mics).
    Handles standard REDCap data/codebook exports, KoboToolbox / ODK XLSForm structures,
    and DHS/MICS hierarchical survey extracts.
    """
    name: str = "Epidemiological Survey Parser (REDCap / Kobo / DHS / MICS)"
    supported_extensions: List[str] = [".redcap", ".kobo", ".dhs", ".mics", ".odk"]
    description: str = "Parses complex survey platforms including REDCap codebooks, KoboToolbox/ODK forms, and DHS/MICS extracts."

    def can_parse(self, filename: str, contents: bytes) -> bool:
        fn_lower = filename.lower()
        if any(fn_lower.endswith(ext) for ext in self.supported_extensions):
            return True
        return False

    def parse(self, filename: str, contents: bytes, **kwargs) -> pd.DataFrame:
        buffer = io.BytesIO(contents)
        fn_lower = filename.lower()
        
        if fn_lower.endswith(".redcap") or fn_lower.endswith(".kobo") or fn_lower.endswith(".odk"):
            # Check if JSON or CSV inside
            try:
                raw_str = contents[:512].decode("utf-8", errors="ignore").strip()
                if raw_str.startswith("[") or raw_str.startswith("{"):
                    buffer.seek(0)
                    return pd.read_json(buffer)
                else:
                    buffer.seek(0)
                    return pd.read_csv(buffer, on_bad_lines="skip")
            except Exception:
                buffer.seek(0)
                return pd.read_excel(buffer)
                
        elif fn_lower.endswith(".dhs") or fn_lower.endswith(".mics"):
            # DHS / MICS extracts are often Stata .dta, SPSS .sav, or flat CSV wrappers
            stata_parser = DataParserRegistry.get_parser("stata")
            spss_parser = DataParserRegistry.get_parser("spss")
            if stata_parser and stata_parser.can_parse(filename, contents):
                return stata_parser.parse(filename, contents, **kwargs)
            if spss_parser and spss_parser.can_parse(filename, contents):
                return spss_parser.parse(filename, contents, **kwargs)
            buffer.seek(0)
            return pd.read_csv(buffer, on_bad_lines="skip")

        buffer.seek(0)
        return pd.read_csv(buffer, on_bad_lines="skip")
