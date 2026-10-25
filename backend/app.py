"""
Deliverable 2: Flask API.

Reads weather data from Firestore and exposes it as JSON for the React frontend.
Also serves Seaborn charts as PNG images (Deliverable 3):
  GET  /api/charts/temperatures | sunshine | conditions | trend?days=7

Run:  python app.py        -> http://localhost:5000

Endpoints:
  GET  /api/health                    simple status check
  GET  /api/cities                    latest reading for every city
  GET  /api/cities/<name>             latest reading for one city
  GET  /api/history?days=7&city=Lahore  daily readings (city optional)
  POST /api/refresh                   re-run the collector, then return latest data
"""
import io
import os
import time
from datetime import date, timedelta

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

import charts
import collect_weather

app = Flask(__name__)
CORS(app)  # allow the React dev server (localhost:3000 / 5173) to call this API

db = collect_weather.init_firestore()

CHART_CACHE_SECONDS = int(os.getenv("CHART_CACHE_SECONDS", "300"))
_chart_cache = {}  # (chart name, days) -> (rendered_at, png bytes)


def latest_cities():
    """All docs from the 'cities' collection, sorted by city name."""
    docs = db.collection("cities").stream()
    return sorted((d.to_dict() for d in docs), key=lambda r: r["city"])


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/cities")
def get_cities():
    return jsonify(latest_cities())


@app.get("/api/cities/<name>")
def get_city(name):
    doc = db.collection("cities").document(name.title()).get()
    if not doc.exists:
        return jsonify({"error": f"City '{name}' not found"}), 404
    return jsonify(doc.to_dict())


@app.get("/api/history")
def get_history():
    try:
        days = max(1, min(int(request.args.get("days", 7)), 90))
    except ValueError:
        return jsonify({"error": "days must be a number"}), 400

    cutoff = (date.today() - timedelta(days=days - 1)).isoformat()
    # Single-field filter only, so no Firestore composite index is needed.
    docs = db.collection("readings").where("date", ">=", cutoff).stream()
    rows = [d.to_dict() for d in docs]

    city = request.args.get("city")
    if city:
        rows = [r for r in rows if r["city"].lower() == city.lower()]

    rows.sort(key=lambda r: (r["date"], r["city"]))
    return jsonify(rows)


def history_rows(days):
    cutoff = (date.today() - timedelta(days=days - 1)).isoformat()
    docs = db.collection("readings").where("date", ">=", cutoff).stream()
    return sorted((d.to_dict() for d in docs), key=lambda r: (r["date"], r["city"]))


@app.get("/api/charts")
def list_charts():
    return jsonify(["temperatures", "sunshine", "conditions", "trend"])


@app.get("/api/charts/<name>")
def get_chart(name):
    """Returns a Seaborn chart as a PNG image. Use directly in <img src=...>."""
    days = None
    if name == "trend":
        try:
            days = max(1, min(int(request.args.get("days", 7)), 90))
        except ValueError:
            days = 7
    elif name not in ("temperatures", "sunshine", "conditions"):
        return jsonify({"error": f"Unknown chart '{name}'"}), 404

    cached = _chart_cache.get((name, days))
    if cached and time.time() - cached[0] < CHART_CACHE_SECONDS:
        png = cached[1]
    else:
        if name == "trend":
            buf = charts.trend_chart(history_rows(days))
        else:
            func = {"temperatures": charts.temperature_chart,
                    "sunshine": charts.sunshine_chart,
                    "conditions": charts.conditions_chart}[name]
            buf = func(latest_cities())
        png = buf.getvalue()
        _chart_cache[(name, days)] = (time.time(), png)

    return send_file(io.BytesIO(png), mimetype="image/png", max_age=0)


@app.post("/api/refresh")
def refresh():
    collect_weather.main()
    _chart_cache.clear()  # new data -> discard rendered charts
    return jsonify(latest_cities())


if __name__ == "__main__":
    app.run(debug=True, port=5000)
