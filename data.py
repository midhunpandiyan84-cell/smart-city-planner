import numpy as np

# Full Tamil Nadu bounds (used as fallback / for the boundary rectangle)
TN_LAT_MIN, TN_LAT_MAX = 8.00, 13.60
TN_LNG_MIN, TN_LNG_MAX = 76.20, 80.40

def generate_population_points(center_lat=None, center_lng=None, spread_km=15, n_clusters=8, points_per_cluster=150):
    """
    If center_lat/center_lng are given, generates population clusters
    concentrated around that point (a specific town/district).
    Otherwise spreads clusters across all of Tamil Nadu.
    """
    np.random.seed(42)
    all_points = []

    if center_lat is not None and center_lng is not None:
        # Convert spread_km roughly to degrees (~111km per degree latitude)
        spread_deg = spread_km / 111.0
        for _ in range(n_clusters):
            cluster_center_lat = np.random.uniform(center_lat - spread_deg, center_lat + spread_deg)
            cluster_center_lng = np.random.uniform(center_lng - spread_deg, center_lng + spread_deg)
            cluster_size = np.random.randint(50, points_per_cluster)
            lats = np.random.normal(cluster_center_lat, spread_deg * 0.15, cluster_size)
            lngs = np.random.normal(cluster_center_lng, spread_deg * 0.15, cluster_size)
            for lat, lng in zip(lats, lngs):
                all_points.append({"lat": lat, "lng": lng, "weight": 1})
    else:
        for _ in range(n_clusters):
            cluster_center_lat = np.random.uniform(TN_LAT_MIN, TN_LAT_MAX)
            cluster_center_lng = np.random.uniform(TN_LNG_MIN, TN_LNG_MAX)
            cluster_size = np.random.randint(50, points_per_cluster)
            lats = np.random.normal(cluster_center_lat, 0.05, cluster_size)
            lngs = np.random.normal(cluster_center_lng, 0.05, cluster_size)
            for lat, lng in zip(lats, lngs):
                all_points.append({"lat": lat, "lng": lng, "weight": 1})

    return all_points

def generate_existing_hospitals(center_lat=None, center_lng=None, spread_km=15, n=2):
    np.random.seed(1)
    if center_lat is not None and center_lng is not None:
        spread_deg = spread_km / 111.0
        return [{"lat": np.random.uniform(center_lat - spread_deg, center_lat + spread_deg),
                  "lng": np.random.uniform(center_lng - spread_deg, center_lng + spread_deg)} for _ in range(n)]
    return [{"lat": np.random.uniform(TN_LAT_MIN, TN_LAT_MAX),
              "lng": np.random.uniform(TN_LNG_MIN, TN_LNG_MAX)} for _ in range(n)]

def generate_unbuildable_zones(center_lat=None, center_lng=None, spread_km=15, n=3):
    np.random.seed(2)
    zones = []
    if center_lat is not None and center_lng is not None:
        spread_deg = spread_km / 111.0
        for _ in range(n):
            zones.append({
                "lat": np.random.uniform(center_lat - spread_deg, center_lat + spread_deg),
                "lng": np.random.uniform(center_lng - spread_deg, center_lng + spread_deg),
                "radius_km": np.random.uniform(0.5, 1.5)
            })
    else:
        for _ in range(n):
            zones.append({
                "lat": np.random.uniform(TN_LAT_MIN, TN_LAT_MAX),
                "lng": np.random.uniform(TN_LNG_MIN, TN_LNG_MAX),
                "radius_km": np.random.uniform(0.5, 1.5)
            })
    return zones