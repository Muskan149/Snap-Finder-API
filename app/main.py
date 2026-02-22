"""
SNAP Retailer Locator API – find top K closest SNAP-accepting retailers
by latitude/longitude or by zip code.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.store_engine import StoreEngine

# Path to CSV (project root)
CSV_PATH = Path(__file__).resolve().parent.parent / "Historical SNAP Retailer Locator Data 2005-2025.csv"

engine: Optional[StoreEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    engine = StoreEngine(CSV_PATH)
    engine.load()
    yield
    engine = None


app = FastAPI(
    title="SNAP Retailer Locator API",
    description="Find the top K closest SNAP-accepting retailers by location (lat/lon) or zip code.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def root():
    """Root: links to API docs and main endpoint."""
    return {
        "message": "SNAP Retailer Locator API",
        "docs": "/docs",
        "health": "/health",
        "closest_retailers": "/retailers/closest?lat=<lat>&lon=<lon>&k=10 or ?zip_code=<zip>&k=10",
    }


class RetailerOut(BaseModel):
    record_id: str
    store_name: str
    store_type: str
    street_number: str
    street_name: str
    additional_address: str
    city: str
    state: str
    zip_code: str
    zip4: str
    county: str
    latitude: float
    longitude: float
    authorization_date: str
    end_date: str
    distance_miles: Optional[float] = None


@app.get("/health")
def health():
    return {"status": "ok", "stores_loaded": engine is not None and engine.is_loaded()}


@app.get(
    "/retailers/closest",
    response_model=List[RetailerOut],
    summary="Top K closest retailers by location or zip",
)
def get_closest_retailers(
    lat: Optional[float] = Query(None, description="Latitude (use with lon)"),
    lon: Optional[float] = Query(None, description="Longitude (use with lat)"),
    zip_code: Optional[str] = Query(None, description="Zip code (alternative to lat/lon)"),
    k: int = Query(10, ge=1, le=100, description="Number of closest retailers to return"),
):
    """
    Return the top K closest SNAP-accepting retailers.

    - **By coordinates**: provide `lat` and `lon`.
    - **By zip code**: provide `zip_code`. The search uses the centroid of retailers in that zip.
    """
    if not engine or not engine.is_loaded():
        raise HTTPException(status_code=503, detail="Store data not loaded")
    if zip_code is not None:
        zip_code = str(zip_code).strip()
    if lat is not None and lon is not None:
        return engine.closest_by_coords(lat=lat, lon=lon, k=k)
    if zip_code:
        return engine.closest_by_zip(zip_code=zip_code, k=k)
    raise HTTPException(
        status_code=400,
        detail="Provide either (lat and lon) or zip_code",
    )
