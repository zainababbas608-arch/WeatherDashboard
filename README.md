# Pakistan Weather Dashboard

Course project in three parts:

1. **Collector** — fetches weather for 7 Pakistani cities from Open-Meteo and stores it in Firebase Firestore.
2. **API** — Flask service exposing the data as JSON, plus Seaborn charts rendered as PNG.
3. **Dashboard** — React frontend showing city cards, highlights and chart tabs.

```
backend/             Flask API, chatbot, weather collector, scheduler, charts
frontend/            React + Vite dashboard
docs/                Lab and Docker guides (Word files)
.github/workflows/   CI checks and GitHub Pages deploy
Dockerfile           One image with the API and the dashboard
docker-compose.yml   Runs that image with your Firebase key
```

## Prerequisites

- Docker Desktop (simplest), or Python 3.12 + Node 20 for local development
- A Firebase project with Firestore enabled

## Firebase key

Download a service account key: **Firebase console → Project settings → Service accounts → Generate new private key**, then save it as `backend/serviceAccountKey.json`.

This file is git-ignored. Never commit or share it.

## Run with Docker

```bash
docker compose up --build
```

- Dashboard: http://localhost:5173
- API: http://localhost:5000/api/health

One container (`weather-app`) runs the Flask API on port 5000 and the dashboard on port 5173. The data refreshes automatically the first time the dashboard is opened each day, or with the **Refresh data** button. For the chatbot's AI mode, put `OPENROUTER_API_KEY` in a `.env` file in the project root (see `backend/env.example`).

## Live site

- Dashboard: GitHub Pages, deployed by `.github/workflows/deploy.yml` on every push to `main`.
- API: hosted on Render from `backend/Dockerfile`. The dashboard finds it through `VITE_API_BASE` in `frontend/.env.production`.

## Run locally

Backend:

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py                # http://localhost:5000
```

Collector (in a second terminal):

```bash
python scheduler.py          # collect now, then every COLLECT_INTERVAL_SECONDS
```

Frontend:

```bash
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

## Data collection

- `python collect_weather.py` writes today's readings for all 7 cities.
- `python collect_weather.py 30` also backfills the last 30 days (0–92 allowed). Safe to re-run: readings are stored per city per date.
- The trend chart's 7/14/30-day views use this history.

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/health` | Status check |
| GET | `/api/cities` | Latest reading for every city |
| GET | `/api/cities/<name>` | Latest reading for one city |
| GET | `/api/history?days=7&city=Lahore` | Daily readings (city optional) |
| GET | `/api/charts/<name>` | Chart PNG: `temperatures`, `sunshine`, `conditions`, `trend?days=7` |
| POST | `/api/refresh` | Re-run the collector, then return latest data |

## Settings (`backend/.env`, see `backend/env.example`)

| Variable | Default | Purpose |
| --- | --- | --- |
| `FIREBASE_KEY_PATH` | `serviceAccountKey.json` | Service account key file |
| `COLLECT_INTERVAL_SECONDS` | `3600` | How often the scheduler collects |
| `CHART_CACHE_SECONDS` | `300` | How long a rendered chart is reused |
| `FLASK_DEBUG` | `0` | `1` enables the debugger (development only) |

## Firestore layout

```
cities/{city}            latest reading, overwritten on every run
readings/{city}_{date}   one document per city per day (history)
```