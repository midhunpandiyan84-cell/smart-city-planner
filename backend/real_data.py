import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def fetch_real_facilities(lat, lng, radius_km, facility_type):
    """
    Fetch REAL facility locations from OpenStreetMap around a given point.
    facility_type maps to OSM tags.
    """
    osm_tag_map = {
        "hospital": 'amenity=hospital',
        "school": 'amenity=school',
        "market": 'shop=supermarket',
        "fire_station": 'amenity=fire_station',
        "water": 'amenity=drinking_water',
    }
    tag = osm_tag_map.get(facility_type, 'amenity=hospital')
    radius_m = int(radius_km * 1000)

    query = f"""
    [out:json][timeout:25];
    (
      node[{tag}](around:{radius_m},{lat},{lng});
      way[{tag}](around:{radius_m},{lat},{lng});
    );
    out center;
    """

    try:
        response = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Overpass API error: {e}")
        return []

    facilities = []
    for element in data.get("elements", []):
        if element["type"] == "node":
            facilities.append({"lat": element["lat"], "lng": element["lon"],
                                "name": element.get("tags", {}).get("name", "Unnamed")})
        elif element["type"] == "way" and "center" in element:
            facilities.append({"lat": element["center"]["lat"], "lng": element["center"]["lon"],
                                "name": element.get("tags", {}).get("name", "Unnamed")})

    return facilities


def fetch_real_water_bodies(lat, lng, radius_km):
    """Fetch real lakes/rivers/reservoirs as unbuildable zones."""
    radius_m = int(radius_km * 1000)
    query = f"""
    [out:json][timeout:25];
    (
      way["natural"="water"](around:{radius_m},{lat},{lng});
      way["landuse"="reservoir"](around:{radius_m},{lat},{lng});
    );
    out center;
    """
    try:
        response = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Overpass API error: {e}")
        return []

    zones = []
    for element in data.get("elements", []):
        if "center" in element:
            zones.append({"lat": element["center"]["lat"], "lng": element["center"]["lon"], "radius_km": 0.6})

    return zones
