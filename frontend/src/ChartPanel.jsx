import { useState } from "react";
import { API } from "./api";

const TABS = [
  { id: "temperatures", label: "Min vs Max" },
  { id: "sunshine", label: "Sunshine" },
  { id: "conditions", label: "Conditions" },
  { id: "trend", label: "Trend" },
];

export default function ChartPanel({ version }) {
  const [tab, setTab] = useState("temperatures");
  const [days, setDays] = useState(7);
  const [failed, setFailed] = useState(false);

  // `version` changes after each refresh so the browser re-fetches the image
  const src =
    `${API}/api/charts/${tab}?v=${version}` + (tab === "trend" ? `&days=${days}` : "");

  const pick = (id) => { setFailed(false); setTab(id); };

  return (
    <section className="panel">
      <div className="tabs" role="tablist">
        {TABS.map((t) => (
          <button key={t.id} role="tab" aria-selected={tab === t.id}
                  className={tab === t.id ? "tab active" : "tab"} onClick={() => pick(t.id)}>
            {t.label}
          </button>
        ))}
        {tab === "trend" && (
          <select value={days} onChange={(e) => { setFailed(false); setDays(Number(e.target.value)); }}
                  aria-label="Days to show">
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
          </select>
        )}
      </div>

      {failed ? (
        <p className="error">Could not load the chart. Is the Flask backend running?</p>
      ) : (
        <img className="chart" src={src} alt={`${tab} chart`} onError={() => setFailed(true)} />
      )}
    </section>
  );
}
