import pandas as pd
import io
import json
import logging
from typing import List
from backend.app.services.data_engine.base import BaseDataParser, DataParserRegistry

logger = logging.getLogger(__name__)


@DataParserRegistry.register("json")
class JSONParser(BaseDataParser):
    """
    JSON / JSON-Lines Data Parser (.json, .jsonl).
    Extracts nested or flat array of records into tabular format.
    """
    name: str = "JSON / JSONL Parser"
    supported_extensions: List[str] = [".json", ".jsonl"]
    description: str = "Parses JSON document structures or newline-delimited JSON records."

    def can_parse(self, filename: str, contents: bytes) -> bool:
        fn_lower = filename.lower()
        if any(fn_lower.endswith(ext) for ext in self.supported_extensions):
            return True
        sample = contents[:512].strip()
        return sample.startswith(b"{") or sample.startswith(b"[")

    def parse(self, filename: str, contents: bytes, **kwargs) -> pd.DataFrame:
        buffer = io.BytesIO(contents)
        if filename.lower().endswith(".jsonl"):
            df = pd.read_json(buffer, lines=True)
        else:
            try:
                df = pd.read_json(buffer)
            except Exception:
                buffer.seek(0)
                raw = json.loads(buffer.read().decode("utf-8", errors="ignore"))
                if isinstance(raw, dict):
                    # Check if keys contain arrays
                    for k, v in raw.items():
                        if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                            return pd.json_normalize(v)
                    df = pd.json_normalize(raw)
                else:
                    df = pd.json_normalize(raw)
        return df
