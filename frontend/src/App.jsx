import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Circle, Popup, Rectangle, useMapEvents, useMap } from "react-leaflet";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import axios from "axios";
import "leaflet/dist/leaflet.css";
import "./leafletIconFix";
import "./App.css";

const API = "http://localhost:8000";

const FACILITY_COLORS = {
  water: "#06b6d4",
  school: "#818cf8",
  hospital: "#22c55e",
  market: "#f59e0b",
  fire_station: "#ec4899",
};

const FACILITY_LABELS = {
  water: "Water Point",
  school: "Primary School",
  hospital: "Hospital",
  market: "Market",
  fire_station: "Fire Station",
};

const TN_BOUNDS = [
  [8.00, 76.20],
  [13.60, 80.40],
];

const TN_CITIES = [
  { name: "Whole Tamil Nadu", lat: null, lng: null },
  { name: "Chennai", lat: 13.0827, lng: 80.2707 },
  { name: "Coimbatore", lat: 11.0168, lng: 76.9558 },
  { name: "Madurai", lat: 9.9252, lng: 78.1198 },
  { name: "Tiruchirappalli", lat: 10.7905, lng: 78.7047 },
  { name: "Salem", lat: 11.6643, lng: 78.1460 },
  { name: "Tirunelveli", lat: 8.7139, lng: 77.7567 },
  { name: "Erode", lat: 11.3410, lng: 77.7172 },
  { name: "Vellore", lat: 12.9165, lng: 79.1325 },
  { name: "Thanjavur", lat: 10.7870, lng: 79.1378 },
];

function isInsideTN(lat, lng) {
  return lat >= 8.00 && lat <= 13.60 && lng >= 76.20 && lng <= 80.40;
}

function ClickHandler({ onMapClick }) {
  useMapEvents({ click(e) { onMapClick(e.latlng); } });
  return null;
}

function FlyTo({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) map.flyTo(center, zoom, { duration: 1.2 });
  }, [center, zoom]);
  return null;
}

function App() {
  const [populationPoints, setPopulationPoints] = useState([]);
  const [unbuildableZones, setUnbuildableZones] = useState([]);
  const [facilitiesByType, setFacilitiesByType] = useState({
    water: [], school: [], hospital: [], market: [], fire_station: [],
  });
  const [suggestions, setSuggestions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [facilityType, setFacilityType] = useState("hospital");
  const [numNew, setNumNew] = useState(1);
  const [placingMode, setPlacingMode] = useState(false);
  const [layers, setLayers] = useState({ population: true, zones: true, facilities: true, suggestions: true });

  const [selectedCity, setSelectedCity] = useState(TN_CITIES[0]);
  const [searchText, setSearchText] = useState("");
  const [searching, setSearching] = useState(false);
  const [mapCenter, setMapCenter] = useState([10.9, 78.3]);
  const [mapZoom, setMapZoom] = useState(7);
  const [activeCenter, setActiveCenter] = useState({ lat: null, lng: null });

  const loadData = async (lat, lng) => {
    const params = lat != null ? { center_lat: lat, center_lng: lng, spread_km: 15 } : {};
    const res = await axios.get(`${API}/api/initial-data`, { params });
    setPopulationPoints(res.data.population_points);
    setUnbuildableZones(res.data.unbuildable_zones);
    setFacilitiesByType(prev => ({ ...prev, hospital: res.data.existing_hospitals }));
    setSuggestions([]);
    setStats(null);
  };

  useEffect(() => { loadData(null, null); }, []);

  const handleCitySelect = (cityName) => {
    const city = TN_CITIES.find(c => c.name === cityName);
    setSelectedCity(city);
    if (city.lat) {
      setMapCenter([city.lat, city.lng]);
      setMapZoom(12);
      setActiveCenter({ lat: city.lat, lng: city.lng });
      loadData(city.lat, city.lng);
    } else {
      setMapCenter([10.9, 78.3]);
      setMapZoom(7);
      setActiveCenter({ lat: null, lng: null });
      loadData(null, null);
    }
  };

  const handleSearch = async () => {
    if (!searchText.trim()) return;
    setSearching(true);
    try {
      const res = await axios.get("https://nominatim.openstreetmap.org/search", {
        params: { q: `${searchText}, Tamil Nadu, India`, format: "json", limit: 1 },
      });
      if (res.data.length === 0) {
        alert("Location not found. Try a different name.");
        setSearching(false);
        return;
      }
      const { lat, lon } = res.data[0];
      const latF = parseFloat(lat), lngF = parseFloat(lon);
      if (!isInsideTN(latF, lngF)) {
        alert("That location seems to be outside Tamil Nadu.");
        setSearching(false);
        return;
      }
      setMapCenter([latF, lngF]);
      setMapZoom(13);
      setActiveCenter({ lat: latF, lng: lngF });
      setSelectedCity({ name: searchText });
      loadData(latF, lngF);
    } catch (err) {
      console.error(err);
      alert("Search failed. Check your internet connection.");
    }
    setSearching(false);
  };

  const handleMapClick = (latlng) => {
    if (!placingMode) return;
    if (!isInsideTN(latlng.lat, latlng.lng)) {
      alert("Please select a location within Tamil Nadu.");
      return;
    }
    setFacilitiesByType(prev => ({
      ...prev,
      [facilityType]: [...prev[facilityType], { lat: latlng.lat, lng: latlng.lng }],
    }));
  };

  const handleSuggest = async () => {
    setLoading(true);
    try {
      const existing = facilitiesByType[facilityType] || [];
      const res = await axios.post(`${API}/api/suggest`, {
        facility_type: facilityType,
        existing_facilities: existing,
        n_new: numNew,
        center_lat: activeCenter.lat,
        center_lng: activeCenter.lng,
        spread_km: 15,
      });
      setSuggestions(res.data.suggestions);
      setStats(res.data);
    } catch (err) {
      console.error(err);
      alert("Error connecting to backend. Check the backend terminal.");
    }
    setLoading(false);
  };

  const toggleLayer = (key) => setLayers(prev => ({ ...prev, [key]: !prev[key] }));

  const chartData = stats ? [
    { name: "Before", km: stats.avg_distance_before_km || 0 },
    { name: "After", km: stats.avg_distance_after_km || 0 },
  ] : [];

  return (
    <div className="app-container">
      <div className="map-area">
        <MapContainer center={mapCenter} zoom={mapZoom} minZoom={7} maxBounds={TN_BOUNDS} maxBoundsViscosity={1.0}
          style={{ height: "100%", width: "100%" }}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <FlyTo center={mapCenter} zoom={mapZoom} />
          <ClickHandler onMapClick={handleMapClick} />
          <Rectangle bounds={TN_BOUNDS} pathOptions={{ color: "#3b82f6", weight: 2, fill: false, dashArray: "6 6" }} />

          {layers.population && populationPoints.map((p, i) => (
            <Circle key={`pop-${i}`} center={[p.lat, p.lng]} radius={activeCenter.lat ? 60 : 300}
              pathOptions={{ color: "#9ca3af", fillOpacity: 0.35, stroke: false }} />
          ))}

          {layers.zones && unbuildableZones.map((z, i) => (
            <Circle key={`zone-${i}`} center={[z.lat, z.lng]} radius={z.radius_km * 1000}
              pathOptions={{ color: "#ef4444", fillOpacity: 0.2, weight: 1 }} />
          ))}

          {layers.facilities && Object.entries(facilitiesByType).map(([type, list]) =>
            list.map((f, i) => (
              <Marker key={`${type}-${i}`} position={[f.lat, f.lng]}>
                <Popup>{FACILITY_LABELS[type]}</Popup>
              </Marker>
            ))
          )}

          {layers.suggestions && suggestions.map((s, i) => (
            <React.Fragment key={`sugg-${i}`}>
              <Marker position={[s.lat, s.lng]}>
                <Popup>Suggested {FACILITY_LABELS[facilityType]} #{s.rank}<br />Serves ~{s.population_served_estimate} points</Popup>
              </Marker>
              <Circle center={[s.lat, s.lng]} radius={activeCenter.lat ? 1500 : 5000}
                pathOptions={{ color: FACILITY_COLORS[facilityType], fillOpacity: 0.12, weight: 2 }} />
            </React.Fragment>
          ))}
        </MapContainer>

        {placingMode && (
          <div className="placing-banner">Click anywhere in Tamil Nadu to place a {FACILITY_LABELS[facilityType]}</div>
        )}
      </div>

      <div className="sidebar">
        <h1 className="title">Smart Town Planner</h1>
        <p className="subtitle">Data-driven infrastructure placement</p>

        <div className="card">
          <label className="field-label">Quick select — city/district</label>
          <select className="select-input" value={selectedCity.name} onChange={e => handleCitySelect(e.target.value)}>
            {TN_CITIES.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
          </select>

          <label className="field-label">Or search any place in Tamil Nadu</label>
          <div style={{ display: "flex", gap: 6 }}>
            <input
              className="select-input"
              placeholder="e.g. Ooty, Kanchipuram..."
              value={searchText}
              onChange={e => setSearchText(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSearch()}
            />
            <button className="btn btn-secondary" style={{ width: 80, marginTop: 0 }} onClick={handleSearch} disabled={searching}>
              {searching ? "..." : "Go"}
            </button>
          </div>
        </div>

        <div className="card">
          <label className="field-label">Facility type</label>
          <select className="select-input" value={facilityType} onChange={e => setFacilityType(e.target.value)}>
            {Object.keys(FACILITY_LABELS).map(key => <option key={key} value={key}>{FACILITY_LABELS[key]}</option>)}
          </select>

          <label className="field-label">Number of new locations</label>
          <select className="select-input" value={numNew} onChange={e => setNumNew(Number(e.target.value))}>
            <option value={1}>1</option><option value={2}>2</option><option value={3}>3</option>
          </select>

          <button className={`btn ${placingMode ? "btn-active" : "btn-secondary"}`} onClick={() => setPlacingMode(!placingMode)}>
            {placingMode ? "✕ Stop placing" : "＋ Place facility on map"}
          </button>

          <button className="btn btn-primary" onClick={handleSuggest} disabled={loading}>
            {loading ? "Calculating..." : `Suggest ${FACILITY_LABELS[facilityType]} location`}
          </button>
        </div>

        {stats && (
          <div className="card">
            <h3 className="card-title">Impact</h3>
            <ResponsiveContainer width="100%" height={140}>
              <BarChart data={chartData}>
                <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} unit="km" />
                <Tooltip contentStyle={{ background: "#1f2937", border: "none" }} />
                <Bar dataKey="km" fill={FACILITY_COLORS[facilityType]} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <div className="stat-row"><span>Underserved population points</span><b>{stats.underserved_count}</b></div>
          </div>
        )}

        <div className="card">
          <h3 className="card-title">Layers</h3>
          {Object.keys(layers).map(key => (
            <label key={key} className="checkbox-row">
              <input type="checkbox" checked={layers[key]} onChange={() => toggleLayer(key)} />
              {key.charAt(0).toUpperCase() + key.slice(1)}
            </label>
          ))}
        </div>

        <div className="card legend-card">
          <h3 className="card-title">Legend</h3>
          <div className="legend-row"><span className="dot" style={{ background: "#9ca3af" }} /> Population</div>
          <div className="legend-row"><span className="dot" style={{ background: "#ef4444" }} /> Unbuildable zone</div>
          <div className="legend-row"><span className="dot" style={{ background: FACILITY_COLORS[facilityType] }} /> Suggested location</div>
        </div>
      </div>
    </div>
  );
}

export default App;