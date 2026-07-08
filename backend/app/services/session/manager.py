import time
import uuid
import threading
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
from backend.app.models.dataset import DatasetSummary, ColumnProfile
from backend.app.models.variables import VariableType
from backend.app.core.exceptions import StatMindException, StatMindErrorLevel


class SessionManager:
    """Thread-safe, in-memory session and dataset manager with TTL and LRU eviction."""
    
    def __init__(self, ttl_seconds: int = 86400, max_cache_mb: float = 512.0):
        self._lock = threading.RLock()
        self._ttl_seconds = ttl_seconds
        self._max_cache_bytes = max_cache_mb * 1024 * 1024
        
        # Internal stores keyed by dataset_id (UUID string)
        self._dataframes: Dict[str, pd.DataFrame] = {}
        self._profiles: Dict[str, DatasetSummary] = {}
        self._access_times: Dict[str, float] = {}

    def _estimate_memory_usage(self) -> int:
        """Estimate total memory used by stored DataFrames in bytes."""
        total_bytes = 0
        for df in self._dataframes.values():
            total_bytes += df.memory_usage(deep=True).sum()
        return int(total_bytes)

    def _evict_if_needed(self, required_bytes: int):
        """Evict oldest datasets if memory threshold is exceeded."""
        while self._dataframes and (self._estimate_memory_usage() + required_bytes > self._max_cache_bytes):
            # Find oldest accessed dataset_id
            oldest_id = min(self._access_times.items(), key=lambda item: item[1])[0]
            self._delete_internal(oldest_id)

    def _delete_internal(self, dataset_id: str):
        self._dataframes.pop(dataset_id, None)
        self._profiles.pop(dataset_id, None)
        self._access_times.pop(dataset_id, None)

    def clear_expired(self):
        """Remove datasets whose access time exceeds TTL."""
        now = time.time()
        with self._lock:
            expired_ids = [
                ds_id for ds_id, last_access in self._access_times.items()
                if now - last_access > self._ttl_seconds
            ]
            for ds_id in expired_ids:
                self._delete_internal(ds_id)

    def save_dataset(self, profile: DatasetSummary, df: pd.DataFrame) -> str:
        """Store a DataFrame and its profile, returning the dataset_id."""
        df_bytes = int(df.memory_usage(deep=True).sum())
        with self._lock:
            self.clear_expired()
            self._evict_if_needed(df_bytes)
            
            dataset_id = profile.dataset_id
            self._dataframes[dataset_id] = df.copy()
            self._profiles[dataset_id] = profile
            self._access_times[dataset_id] = time.time()
            return dataset_id

    def get_dataset(self, dataset_id: str) -> Tuple[DatasetSummary, pd.DataFrame]:
        """Retrieve dataset profile and DataFrame by dataset_id."""
        with self._lock:
            if dataset_id not in self._dataframes or dataset_id not in self._profiles:
                raise StatMindException(
                    error_code="FileNotFoundError",
                    level=StatMindErrorLevel.USER_ERROR
                )
            self._access_times[dataset_id] = time.time()
            return self._profiles[dataset_id], self._dataframes[dataset_id].copy()

    def list_datasets(self) -> List[DatasetSummary]:
        """List all active dataset profiles."""
        with self._lock:
            self.clear_expired()
            return list(self._profiles.values())

    def delete_dataset(self, dataset_id: str) -> bool:
        """Delete a dataset by ID."""
        with self._lock:
            if dataset_id in self._dataframes:
                self._delete_internal(dataset_id)
                return True
            return False

    def update_variable_type(self, dataset_id: str, var_name: str, new_type: VariableType) -> DatasetSummary:
        """Update the detected VariableType of a specific column."""
        with self._lock:
            if dataset_id not in self._profiles:
                raise StatMindException(error_code="FileNotFoundError", level=StatMindErrorLevel.USER_ERROR)
            
            profile = self._profiles[dataset_id]
            col_profile = next((col for col in profile.variables if col.name == var_name), None)
            if not col_profile:
                raise StatMindException(
                    error_code="VariableNotFound",
                    level=StatMindErrorLevel.USER_ERROR,
                    format_kwargs={"variable_name": var_name, "available_variables": ", ".join([c.name for c in profile.variables])}
                )
            
            col_profile.detected_type = new_type
            self._access_times[dataset_id] = time.time()
            return profile

    def clean_dataset(self, dataset_id: str, drop_duplicates: bool = False, dropna_cols: Optional[List[str]] = None) -> DatasetSummary:
        """Perform automated data cleaning on the cached dataset."""
        with self._lock:
            if dataset_id not in self._dataframes:
                raise StatMindException(error_code="FileNotFoundError", level=StatMindErrorLevel.USER_ERROR)
            
            df = self._dataframes[dataset_id]
            if drop_duplicates:
                df = df.drop_duplicates()
            if dropna_cols:
                df = df.dropna(subset=dropna_cols)
                
            self._dataframes[dataset_id] = df
            # Update n_rows in profile
            profile = self._profiles[dataset_id]
            profile.n_rows = len(df)
            self._access_times[dataset_id] = time.time()
            return profile


# Global singleton instance
session_manager = SessionManager()
