from abc import ABC, abstractmethod
from typing import Dict, List, Type, Any, Optional
import pandas as pd
import io
import logging

logger = logging.getLogger(__name__)


class BaseDataParser(ABC):
    """
    Abstract base class for all StatAid Studio data parsers.
    Every data format (CSV, Excel, SPSS, Stata, SAS, RData, Parquet, JSON, Survey formats)
    implements this unified interface.
    """
    name: str = "Base Parser"
    supported_extensions: List[str] = []
    description: str = "Abstract data parser"
    requires_external_lib: Optional[str] = None

    @abstractmethod
    def can_parse(self, filename: str, contents: bytes) -> bool:
        """Check if this parser can handle the file based on extension or header magic bytes."""
        pass

    @abstractmethod
    def parse(self, filename: str, contents: bytes, **kwargs) -> pd.DataFrame:
        """Parse the binary file contents into a clean pandas DataFrame with recovered variable metadata."""
        pass

    def get_metadata_manifest(self) -> Dict[str, Any]:
        """Return structured metadata about this parser module."""
        return {
            "name": self.name,
            "supported_extensions": self.supported_extensions,
            "description": self.description,
            "requires_external_lib": self.requires_external_lib,
            "module_type": "DataParser"
        }


class DataParserRegistry:
    """
    Modular registry for all data import parsers.
    Nothing is hardcoded: parsers self-register dynamically on startup or via plugins.
    """
    _parsers: Dict[str, Type[BaseDataParser]] = {}
    _instances: Dict[str, BaseDataParser] = {}

    @classmethod
    def register(cls, parser_id: str):
        """Decorator to register a data parser class in the modular engine."""
        def decorator(parser_cls: Type[BaseDataParser]):
            cls._parsers[parser_id.lower()] = parser_cls
            cls._instances[parser_id.lower()] = parser_cls()
            logger.info(f"Registered DataParser: [{parser_id}] -> {parser_cls.__name__}")
            return parser_cls
        return decorator

    @classmethod
    def get_parser(cls, parser_id: str) -> Optional[BaseDataParser]:
        """Retrieve a specific parser instance by exact ID."""
        return cls._instances.get(parser_id.lower())

    @classmethod
    def list_parsers(cls) -> List[Dict[str, Any]]:
        """List all registered data parsers and their supported file extensions."""
        return [
            {"id": pid, **instance.get_metadata_manifest()}
            for pid, instance in cls._instances.items()
        ]

    @classmethod
    def parse_file(cls, filename: str, contents: bytes, **kwargs) -> pd.DataFrame:
        """
        Dynamically select and execute the appropriate parser for the file.
        Iterates across registered modular parsers without any hardcoded extension assumptions.
        """
        filename_lower = filename.lower()
        
        # 1. Check exact extension matches first
        for pid, instance in cls._instances.items():
            if any(filename_lower.endswith(ext) for ext in instance.supported_extensions):
                try:
                    logger.info(f"Attempting parse of '{filename}' using {instance.name} ({pid})")
                    return instance.parse(filename, contents, **kwargs)
                except Exception as e:
                    logger.warning(f"Parser {instance.name} failed on '{filename}': {e}. Trying fallback parsers...")

        # 2. Check header magic bytes / can_parse checks
        for pid, instance in cls._instances.items():
            try:
                if instance.can_parse(filename, contents):
                    return instance.parse(filename, contents, **kwargs)
            except Exception:
                continue

        # 3. Ultimate Fallback to CSV resilient parser
        csv_parser = cls._instances.get("csv")
        if csv_parser:
            return csv_parser.parse(filename, contents, **kwargs)

        raise ValueError(f"No modular DataParser could successfully decode dataset '{filename}'.")
