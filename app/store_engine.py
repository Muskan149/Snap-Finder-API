"""
Store engine: load CSV, filter valid coordinates, compute distances (Haversine),
and return top K closest by lat/lon or by zip code.
"""

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Earth radius in miles
EARTH_RADIUS_MILES = 3958.8


def haversine_miles(
    lat1: np.ndarray, lon1: np.ndarray, lat2: float, lon2: float
) -> np.ndarray:
    """Vectorized Haversine distance in miles from (lat1, lon1) to (lat2, lon2)."""
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.minimum(np.sqrt(np.maximum(a, 0)), 1.0))
    return EARTH_RADIUS_MILES * c


class StoreEngine:
    def __init__(self, csv_path: Path):
        self.csv_path = Path(csv_path)
        self._df: Optional[pd.DataFrame] = None
        self._valid: Optional[pd.DataFrame] = None  # rows with valid lat/lon

    def load(self) -> None:
        df = pd.read_csv(
            self.csv_path,
            dtype={
                "Record ID": str,
                "Store Name": str,
                "Store Type": str,
                "Street Number": str,
                "Street Name": str,
                "Additional Address": str,
                "City": str,
                "State": str,
                "Zip Code": str,
                "Zip4": str,
                "County": str,
                "Latitude": np.float64,
                "Longitude": np.float64,
                "Authorization Date": str,
                "End Date": str,
            },
            na_values=["", " "],
            keep_default_na=True,
        )
        # Normalize zip for lookup (strip, string)
        df["Zip Code"] = df["Zip Code"].astype(str).str.strip()
        # Keep only rows with valid coordinates (exclude 0,0 and NaN)
        valid = df.dropna(subset=["Latitude", "Longitude"])
        valid = valid[((valid["Latitude"] != 0) | (valid["Longitude"] != 0))]
        self._df = df
        self._valid = valid.reset_index(drop=True)

    def is_loaded(self) -> bool:
        return self._valid is not None and len(self._valid) > 0

    def closest_by_coords(self, lat: float, lon: float, k: int) -> list[dict]:
        """Return top K retailers closest to (lat, lon)."""
        if self._valid is None or self._valid.empty:
            return []
        dist = haversine_miles(
            self._valid["Latitude"].values,
            self._valid["Longitude"].values,
            lat,
            lon,
        )
        order = np.argsort(dist)[:k]
        return self._rows_to_response(self._valid.iloc[order], dist[order])

    def closest_by_zip(self, zip_code: str, k: int) -> list[dict]:
        """
        Return top K retailers closest to the centroid of all retailers in the given zip.
        If no retailers in zip, returns empty list.
        """
        if self._valid is None or self._valid.empty:
            return []
        in_zip = self._valid[self._valid["Zip Code"] == zip_code]
        if in_zip.empty:
            return []
        center_lat = in_zip["Latitude"].mean()
        center_lon = in_zip["Longitude"].mean()
        dist = haversine_miles(
            self._valid["Latitude"].values,
            self._valid["Longitude"].values,
            center_lat,
            center_lon,
        )
        order = np.argsort(dist)[:k]
        return self._rows_to_response(self._valid.iloc[order], dist[order])

    def _rows_to_response(self, subset: pd.DataFrame, distances: np.ndarray) -> list[dict]:
        out = []
        for i, (_, row) in enumerate(subset.iterrows()):
            d = float(distances[i]) if i < len(distances) else None
            out.append({
                "record_id": str(row["Record ID"]),
                "store_name": str(row["Store Name"]),
                "store_type": str(row["Store Type"]),
                "street_number": str(row["Street Number"]),
                "street_name": str(row["Street Name"]),
                "additional_address": str(row["Additional Address"]),
                "city": str(row["City"]),
                "state": str(row["State"]),
                "zip_code": str(row["Zip Code"]),
                "zip4": str(row["Zip4"]) if pd.notna(row["Zip4"]) else "",
                "county": str(row["County"]),
                "latitude": float(row["Latitude"]),
                "longitude": float(row["Longitude"]),
                "authorization_date": str(row["Authorization Date"]) if pd.notna(row["Authorization Date"]) else "",
                "end_date": str(row["End Date"]) if pd.notna(row["End Date"]) else "",
                "distance_miles": d,
            })
        return out
