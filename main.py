from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import data, planner, real_data
from tn_population import TN_DISTRICT_POPULATION, get_population_weight
import numpy as np

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Facility(BaseModel):
    lat: float
    lng: float

class SuggestRequest(BaseModel):
    facility_type: str = "hospital"
    existing_facilities: List[Facility]
    n_new: int = 1
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    spread_km: float = 15

def generate_realistic_population(center_lat, center_lng, spread_km, n_points=300):
    """
    Generates population points weighted by REAL district population data.
    Denser clustering near the actual district's real population figure.
    """
    weight = get_population_weight(center_lat, center_lng)
    # Scale point density based on real population (more people = denser simulated points)
    density_factor = min(weight / 500000, 3.0)  # cap the multiplier
    actual_n_points = int(n_points * density_factor)

    spread_deg = spread_km / 111.0
    np.random.seed(int(center_lat * 1000) + int(center_lng * 1000))  # consistent per location
    lats = np.random.normal(center_lat, spread_deg * 0.3, actual_n_points)
    lngs = np.random.normal(center_lng, spread_deg * 0.3, actual_n_points)
    return [{"lat": float(la), "lng": float(ln), "weight": 1} for la, ln in zip(lats, lngs)]

@app.get("/api/districts")
def get_districts():
    """Return real TN district data with actual population figures."""
    return TN_DISTRICT_POPULATION

@app.get("/api/initial-data")
def initial_data(center_lat: Optional[float] = None, center_lng: Optional[float] = None,
                  spread_km: float = 15, use_real_data: bool = True):
    if center_lat is not None and center_lng is not None:
        if use_real_data:
            # REAL hospitals from OpenStreetMap
            real_hospitals = real_data.fetch_real_facilities(center_lat, center_lng, spread_km, "hospital")
            real_water = real_data.fetch_real_water_bodies(center_lat, center_lng, spread_km)
            population_points = generate_realistic_population(center_lat, center_lng, spread_km)
            return {
                "population_points": population_points,
                "existing_hospitals": real_hospitals[:15],  # cap for performance
                "unbuildable_zones": real_water[:10],
                "data_source": "real"
            }
        else:
            population_points = generate_realistic_population(center_lat, center_lng, spread_km)
            return {
                "population_points": population_points,
                "existing_hospitals": data.generate_existing_hospitals(center_lat, center_lng, spread_km),
                "unbuildable_zones": data.generate_unbuildable_zones(center_lat, center_lng, spread_km),
                "data_source": "synthetic"
            }
    else:
        return {
            "population_points": data.generate_population_points(),
            "existing_hospitals": data.generate_existing_hospitals(),
            "unbuildable_zones": data.generate_unbuildable_zones(),
            "data_source": "synthetic"
        }

@app.get("/api/facility-types")
def facility_types():
    return planner.FACILITY_CONFIG

@app.post("/api/suggest")
def suggest(req: SuggestRequest):
    config = planner.FACILITY_CONFIG.get(req.facility_type, planner.FACILITY_CONFIG["hospital"])
    radius = config["radius_km"]

    if req.center_lat is not None:
        population_points = generate_realistic_population(req.center_lat, req.center_lng, req.spread_km)
        unbuildable_zones = real_data.fetch_real_water_bodies(req.center_lat, req.center_lng, req.spread_km)
    else:
        population_points = data.generate_population_points()
        unbuildable_zones = data.generate_unbuildable_zones()

    existing = [f.dict() for f in req.existing_facilities]

    underserved = planner.find_underserved_points(population_points, existing, radius)
    suggestions = planner.suggest_new_facilities(underserved, unbuildable_zones, req.n_new)

    avg_before = planner.calculate_avg_distance(population_points, existing)
    new_facilities = existing + [{"lat": s["lat"], "lng": s["lng"]} for s in suggestions]
    avg_after = planner.calculate_avg_distance(population_points, new_facilities)

    return {
        "facility_type": req.facility_type,
        "suggestions": suggestions,
        "avg_distance_before_km": round(avg_before, 2) if avg_before else None,
        "avg_distance_after_km": round(avg_after, 2),
        "underserved_count": len(underserved)
    }