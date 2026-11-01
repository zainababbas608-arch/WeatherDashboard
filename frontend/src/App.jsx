import { useEffect, useMemo, useState } from "react";
import { getCities, refreshCities } from "./api";
import CityCard from "./CityCard.jsx";
import ChartPanel from "./ChartPanel.jsx";
import ChatBot from "./ChatBot.jsx";

export default function App() {
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);

  useEffect(() => {
    getCities()
      .then(setCities)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    setError("");
    try {
      setCities(await refreshCities());
      setVersion((v) => v + 1);
    } catch (e) {
      setError(e.message);
    } finally {
      setRefreshing(false);
    }
  };

  const highlights = useMemo(() => {
    if (!cities.length) return null;
    const by = (key, dir) => [...cities].sort((a, b) => dir * (b[key] - a[key]))[0];
    return {
      hottest: by("temp_max_c", 1),
      coldest: by("temp_min_c", -1),
      sunniest: by("sunshine_hours", 1),
    };
  }, [cities]);

  return (
    <main className="app">
      <header className="top">
        <div>
          <h1>Pakistan Weather Dashboard</h1>
          <p className="sub">
            Seven cities · data from Open-Meteo · stored in Firebase Firestore
            {cities[0] && <> · {cities[0].date}</>}
          </p>
        </div>
        <button className="refresh" onClick={onRefresh} disabled={refreshing}>
          {refreshing ? "Updating…" : "↻ Refresh data"}
        </button>
      </header>

      {error && <p className="error">{error}. Make sure the Flask API is running on port 5000.</p>}
      {loading && <p className="muted">Loading weather…</p>}
      {!loading && !error && cities.length === 0 && (
        <p className="muted">No data yet. Click “Refresh data” (or run collect_weather.py).</p>
      )}

      {highlights && (
        <section className="highlights">
          <div><span>🔥 Hottest</span><strong>{highlights.hottest.city}</strong>
            <em>{Math.round(highlights.hottest.temp_max_c)}° max</em></div>
          <div><span>🧊 Coolest nights</span><strong>{highlights.coldest.city}</strong>
            <em>{Math.round(highlights.coldest.temp_min_c)}° min</em></div>
          <div><span>☀️ Sunniest</span><strong>{highlights.sunniest.city}</strong>
            <em>{highlights.sunniest.sunshine_hours} h sun</em></div>
        </section>
      )}

      <section className="grid">
        {cities.map((c) => <CityCard key={c.city} city={c} />)}
      </section>

      {cities.length > 0 && <ChartPanel version={version} />}

      <ChatBot />
    </main>
  );
}
