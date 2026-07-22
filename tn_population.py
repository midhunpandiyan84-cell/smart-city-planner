# Real Tamil Nadu district population data (2011 Census, in absolute numbers)
# Source: Census of India 2011, Tamil Nadu district-wise population
TN_DISTRICT_POPULATION = {
    "Chennai": {"lat": 13.0827, "lng": 80.2707, "population": 4646732},
    "Coimbatore": {"lat": 11.0168, "lng": 76.9558, "population": 3458045},
    "Madurai": {"lat": 9.9252, "lng": 78.1198, "population": 3038252},
    "Tiruchirappalli": {"lat": 10.7905, "lng": 78.7047, "population": 2722290},
    "Salem": {"lat": 11.6643, "lng": 78.1460, "population": 3482056},
    "Tirunelveli": {"lat": 8.7139, "lng": 77.7567, "population": 3072880},
    "Erode": {"lat": 11.3410, "lng": 77.7172, "population": 2251744},
    "Vellore": {"lat": 12.9165, "lng": 79.1325, "population": 3936331},
    "Thanjavur": {"lat": 10.7870, "lng": 79.1378, "population": 2405890},
    "Dindigul": {"lat": 10.3624, "lng": 77.9695, "population": 2159775},
    "Kanchipuram": {"lat": 12.8342, "lng": 79.7036, "population": 3998252},
    "Cuddalore": {"lat": 11.7480, "lng": 79.7714, "population": 2605914},
    "Villupuram": {"lat": 11.9401, "lng": 79.4861, "population": 3458873},
    "Thoothukudi": {"lat": 8.7642, "lng": 78.1348, "population": 1750176},
    "Nagapattinam": {"lat": 10.7660, "lng": 79.8420, "population": 1616450},
}

def get_population_weight(lat, lng):
    """Find nearest district and return its population as a weight multiplier."""
    import math
    closest_district = None
    min_dist = float("inf")
    for name, info in TN_DISTRICT_POPULATION.items():
        dist = math.sqrt((lat - info["lat"])**2 + (lng - info["lng"])**2)
        if dist < min_dist:
            min_dist = dist
            closest_district = info
    return closest_district["population"] if closest_district else 1000000