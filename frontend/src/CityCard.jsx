export function conditionIcon(condition = "", isDay = true) {
  const c = condition.toLowerCase();
  if (c.includes("thunder")) return "⛈️";
  if (c.includes("snow")) return "❄️";
  if (c.includes("rain") || c.includes("drizzle") || c.includes("shower")) return "🌧️";
  if (c.includes("fog")) return "🌫️";
  if (c.includes("overcast")) return "☁️";
  if (c.includes("partly")) return isDay ? "⛅" : "☁️";
  if (c.includes("clear")) return isDay ? "☀️" : "🌙";
  return "🌡️";
}

const STATUS_CLASS = {
  "Sunny": "sunny",
  "Partly sunny": "partly",
  "Mostly cloudy": "cloudy",
};

export default function CityCard({ city }) {
  const {
    city: name, condition, is_day, temp_current_c, temp_min_c, temp_max_c,
    sunshine_hours, sunshine_pct, sunshine_status,
  } = city;

  return (
    <article className="card">
      <header className="card-head">
        <h3>{name}</h3>
        <span className="icon" aria-hidden="true">{conditionIcon(condition, is_day)}</span>
      </header>

      <p className="temp-now">{Math.round(temp_current_c)}°<small>C now</small></p>
      <p className="condition">{condition}</p>

      <div className="range">
        <span className="min">▼ {Math.round(temp_min_c)}°</span>
        <span className="max">▲ {Math.round(temp_max_c)}°</span>
      </div>

      <div className="sun">
        <div className="sun-row">
          <span className={`badge ${STATUS_CLASS[sunshine_status] || ""}`}>{sunshine_status}</span>
          <span className="sun-hours">{sunshine_hours} h sun</span>
        </div>
        <div className="bar" role="img" aria-label={`${sunshine_pct}% of daylight is sunny`}>
          <div className="bar-fill" style={{ width: `${Math.min(sunshine_pct, 100)}%` }} />
        </div>
      </div>
    </article>
  );
}
