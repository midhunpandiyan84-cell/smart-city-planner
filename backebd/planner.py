import numpy as np
from sklearn.cluster import KMeans
from geopy.distance import geodesic

FACILITY_CONFIG = {
    "water": {"radius_km": 1, "label": "Water Point"},
    "school": {"radius_km": 2, "label": "Primary School"},
    "hospital": {"radius_km": 5, "label": "Hospital"},
    "market": {"radius_km": 3, "label": "Market"},
    "fire_station": {"radius_km": 5, "label": "Fire Station"},
}

def haversine_km(lat1, lng1, lat2, lng2):
    return geodesic((lat1, lng1), (lat2, lng2)).km

def find_underserved_points(population_points, existing_facilities, service_radius_km=5):
    underserved = []
    for p in population_points:
        if not existing_facilities:
            underserved.append(p)
            continue
        min_dist = min(haversine_km(p["lat"], p["lng"], f["lat"], f["lng"]) for f in existing_facilities)
        if min_dist > service_radius_km:
            underserved.append(p)
    return underserved

def is_in_unbuildable_zone(lat, lng, unbuildable_zones):
    return any(haversine_km(lat, lng, z["lat"], z["lng"]) < z["radius_km"] for z in unbuildable_zones)

def suggest_new_facilities(underserved_points, unbuildable_zones, n_new=1):
    if len(underserved_points) < n_new:
        return []
    coords = np.array([[p["lat"], p["lng"]] for p in underserved_points])
    kmeans = KMeans(n_clusters=n_new, n_init=10, random_state=0).fit(coords)

    suggestions = []
    for i, center in enumerate(kmeans.cluster_centers_):
        lat, lng = center
        attempts = 0
        while is_in_unbuildable_zone(lat, lng, unbuildable_zones) and attempts < 5:
            lat += np.random.uniform(-0.01, 0.01)
            lng += np.random.uniform(-0.01, 0.01)
            attempts += 1
        suggestions.append({
            "lat": lat, "lng": lng,
            "population_served_estimate": int(np.sum(kmeans.labels_ == i)),
            "rank": i + 1
        })
    suggestions.sort(key=lambda x: -x["population_served_estimate"])
    return suggestions

def calculate_avg_distance(population_points, facilities):
    if not facilities:
        return None
    dists = [min(haversine_km(p["lat"], p["lng"], f["lat"], f["lng"]) for f in facilities) for p in population_points]
    return float(np.mean(dists))
