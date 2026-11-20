"""
Data loader module for Earth Data Lab.
Handles reading, validating, caching, and filtering climate datasets.
"""

import json
import os
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple


METADATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'metadata.json')


class DatasetValidationError(Exception):
    """Raised when a dataset fails schema or integrity validation."""
    pass


class DataLoader:
    """Manages loading, validation, and querying of climate datasets."""
    
    def __init__(self, metadata_path: str = METADATA_PATH):
        self.metadata_path = metadata_path
        self.metadata = self._load_metadata()
        self._cache: Dict[str, pd.DataFrame] = {}

    def _load_metadata(self) -> Dict[str, Any]:
        """Loads dataset metadata registry."""
        if not os.path.exists(self.metadata_path):
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_path}")
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_available_datasets(self) -> Dict[str, Any]:
        """Returns metadata for all available datasets."""
        return self.metadata.get("datasets", {})

    def get_dataset_metadata(self, dataset_id: str) -> Dict[str, Any]:
        """Returns metadata for a specific dataset ID."""
        datasets = self.get_available_datasets()
        if dataset_id not in datasets:
            raise KeyError(f"Unknown dataset ID: {dataset_id}. Available: {list(datasets.keys())}")
        return datasets[dataset_id]

    def load_dataset(self, dataset_id: str = "nasa_gistemp", reload: bool = False) -> pd.DataFrame:
        """
        Loads and validates a dataset by ID.
        Returns a cleaned, validated Pandas DataFrame.
        """
        if not reload and dataset_id in self._cache:
            return self._cache[dataset_id].copy()

        meta = self.get_dataset_metadata(dataset_id)
        rel_path = meta.get("file_path")
        base_dir = os.path.dirname(os.path.dirname(__file__))
        full_path = os.path.join(base_dir, rel_path)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Dataset file not found at {full_path}")

        try:
            df = pd.read_csv(full_path)
        except Exception as e:
            raise DatasetValidationError(f"Failed to read CSV at {full_path}: {e}")

        # Validate Schema
        required_cols = {"year", "annual_anomaly", "five_year_smooth", "uncertainty"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            raise DatasetValidationError(f"Dataset is missing required columns: {missing_cols}")

        # Data types and sanitization
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df['annual_anomaly'] = pd.to_numeric(df['annual_anomaly'], errors='coerce')
        df['five_year_smooth'] = pd.to_numeric(df['five_year_smooth'], errors='coerce')
        df['uncertainty'] = pd.to_numeric(df['uncertainty'], errors='coerce')

        # Drop rows with invalid years or anomalies
        df = df.dropna(subset=['year', 'annual_anomaly'])
        df['year'] = df['year'].astype(int)

        # Ensure sorted monotonically by year
        df = df.sort_values(by='year').reset_index(drop=True)

        if len(df) == 0:
            raise DatasetValidationError(f"Dataset {dataset_id} contains 0 valid rows.")

        self._cache[dataset_id] = df
        return df.copy()

    def get_filtered_data(
        self,
        dataset_id: str = "nasa_gistemp",
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Retrieves filtered data and accompanying metadata.
        """
        df = self.load_dataset(dataset_id)
        meta = self.get_dataset_metadata(dataset_id)

        min_avail = int(df['year'].min())
        max_avail = int(df['year'].max())

        start = start_year if start_year is not None else min_avail
        end = end_year if end_year is not None else max_avail

        # Clamp and validate ranges
        if start > end:
            start, end = end, start

        filtered_df = df[(df['year'] >= start) & (df['year'] <= end)].copy()

        summary_meta = {
            **meta,
            "query_start_year": start,
            "query_end_year": end,
            "min_available_year": min_avail,
            "max_available_year": max_avail,
            "record_count": len(filtered_df)
        }

        return filtered_df, summary_meta
