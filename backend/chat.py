"""
Analytics chatbot.

POST /api/chat   body: {"message": "which city is hottest?", "history": [{"role","content"}, ...]}
                 returns: {"reply": "...", "source": "rules" | "openrouter"}

Works in two modes:
  * No API key  -> rule-based answers computed from your Firestore data (free, offline logic).
  * OPENROUTER_API_KEY set (in backend/.env) -> an OpenRouter model answers using your data as context.
    If the API call fails, it falls back to the rule-based answer automatically.
"""
import json
import os
import re
from statistics import mean

import requests
from flask import jsonify, request

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# Change the model in backend/.env with OPENROUTER_MODEL=... (see openrouter.ai/models)
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")


# ---------- rule-based analytics ----------
def _t(x):
    return f"{x:.0f}°C"


def rule_answer(msg, rows, hist):
    m = msg.lower()
    names = {r["city"].lower(): r for r in rows}
    mentioned = [names[n] for n in names if n in m]
    top = lambda key, rev=True: sorted(rows, key=lambda r: r[key], reverse=rev)

    # compare two cities
    if len(mentioned) >= 2 or ("compare" in m and mentioned):
        a, b = (mentioned + [None, None])[:2]
        if b is None:
            return "Tell me two cities to compare, for example: compare Karachi and Lahore."
        warmer = a if a["temp_max_c"] >= b["temp_max_c"] else b
        sunnier = a if a["sunshine_hours"] >= b["sunshine_hours"] else b
        return (f"{a['city']}: {_t(a['temp_min_c'])} to {_t(a['temp_max_c'])}, {a['condition']}, "
                f"{a['sunshine_hours']} h sun.\n"
                f"{b['city']}: {_t(b['temp_min_c'])} to {_t(b['temp_max_c'])}, {b['condition']}, "
                f"{b['sunshine_hours']} h sun.\n"
                f"{warmer['city']} is warmer and {sunnier['city']} gets more sunshine.")

    # single city
    if len(mentioned) == 1:
        c = mentioned[0]
        return (f"{c['city']} today: {c['condition']}, currently {_t(c['temp_current_c'])} "
                f"(low {_t(c['temp_min_c'])}, high {_t(c['temp_max_c'])}). "
                f"Sunshine: {c['sunshine_status']} ({c['sunshine_hours']} h, {c['sunshine_pct']}% of daylight).")

    if any(w in m for w in ("hottest", "warmest", "highest temp", "hot")):
        c = top("temp_max_c")[0]
        return f"{c['city']} is the hottest today with a high of {_t(c['temp_max_c'])}."
    if any(w in m for w in ("coldest", "coolest", "lowest", "cold", "cool")):
        c = top("temp_min_c", False)[0]
        return f"{c['city']} is the coolest, with a low of {_t(c['temp_min_c'])}."
    if any(w in m for w in ("sunniest", "most sun", "sunshine", "sunny")):
        c = top("sunshine_hours")[0]
        d = top("sunshine_hours", False)[0]
        return (f"{c['city']} is the sunniest with {c['sunshine_hours']} h of sunshine ({c['sunshine_status']}). "
                f"{d['city']} has the least at {d['sunshine_hours']} h.")
    if any(w in m for w in ("average", "mean", "overall")):
        return (f"Across {len(rows)} cities: average high {_t(mean(r['temp_max_c'] for r in rows))}, "
                f"average low {_t(mean(r['temp_min_c'] for r in rows))}, "
                f"average sunshine {mean(r['sunshine_hours'] for r in rows):.1f} h.")
    if any(w in m for w in ("range", "difference", "swing", "variation")):
        c = max(rows, key=lambda r: r["temp_max_c"] - r["temp_min_c"])
        return f"{c['city']} has the widest daily range: {_t(c['temp_min_c'])} to {_t(c['temp_max_c'])} ({c['temp_max_c'] - c['temp_min_c']:.0f}° swing)."
    if any(w in m for w in ("rain", "storm", "wet", "cloud", "condition", "weather like")):
        groups = {}
        for r in rows:
            groups.setdefault(r["condition"], []).append(r["city"])
        return "Current conditions: " + "; ".join(f"{k}: {', '.join(v)}" for k, v in groups.items()) + "."
    if any(w in m for w in ("trend", "history", "week", "days", "change")):
        days = sorted({h["date"] for h in hist})
        if len(days) < 2:
            return "I only have one day of data so far. Run the collector on more days to see trends."
        first, last = days[0], days[-1]
        out = []
        for r in rows:
            a = [h for h in hist if h["city"] == r["city"] and h["date"] == first]
            b = [h for h in hist if h["city"] == r["city"] and h["date"] == last]
            if a and b:
                out.append((r["city"], b[0]["temp_max_c"] - a[0]["temp_max_c"]))
        out.sort(key=lambda x: -x[1])
        return (f"From {first} to {last}, highs changed the most in {out[0][0]} ({out[0][1]:+.0f}°) "
                f"and the least in {out[-1][0]} ({out[-1][1]:+.0f}°).")
    if any(w in m for w in ("summary", "summarize", "overview", "all cities", "report")):
        c, d, s = top("temp_max_c")[0], top("temp_min_c", False)[0], top("sunshine_hours")[0]
        return (f"Summary for {rows[0]['date']}: hottest {c['city']} ({_t(c['temp_max_c'])}), "
                f"coolest {d['city']} (low {_t(d['temp_min_c'])}), sunniest {s['city']} ({s['sunshine_hours']} h). "
                f"Average high is {_t(mean(r['temp_max_c'] for r in rows))}.")
    return ("I can answer questions about the 7 cities. Try: “Which city is hottest?”, "
            "“Compare Karachi and Lahore”, “Average temperature”, “Which city has the most sunshine?”, "
            "“Weather in Quetta” or “Give me a summary”.")


# ---------- OpenRouter mode ----------
def llm_answer(msg, rows, hist, convo):
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        return None
    slim = [{k: r[k] for k in ("city", "date", "temp_min_c", "temp_max_c", "temp_current_c",
                               "condition", "sunshine_hours", "sunshine_pct", "sunshine_status")} for r in rows]
    hist_slim = [{k: h.get(k) for k in ("city", "date", "temp_min_c", "temp_max_c", "sunshine_hours")} for h in hist]
    system = ("You are a weather analytics assistant for a dashboard covering 7 cities of Pakistan. "
              "Answer only from the data below. Be concise (under 120 words), use numbers, and say so if "
              "the data cannot answer the question.\n\nLATEST DATA:\n" + json.dumps(slim) +
              "\n\nHISTORY (daily):\n" + json.dumps(hist_slim))
    messages = [{"role": "system", "content": system}]
    messages += [{"role": m["role"], "content": m["content"]} for m in convo
                 if m.get("role") in ("user", "assistant") and m.get("content")][-6:]
    messages.append({"role": "user", "content": msg})
    resp = requests.post(OPENROUTER_URL, timeout=40, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": OPENROUTER_MODEL, "max_tokens": 400, "messages": messages})
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    return (text or "").strip() or None


def register_chat(app, get_latest, get_history):
    @app.post("/api/chat")
    def chat():
        body = request.get_json(silent=True) or {}
        msg = (body.get("message") or "").strip()[:500]
        if not msg:
            return jsonify({"error": "message is required"}), 400
        rows = get_latest()
        if not rows:
            return jsonify({"reply": "There is no weather data yet. Click “Refresh data” first.", "source": "rules"})
        hist = get_history(7)
        try:
            reply = llm_answer(msg, rows, hist, body.get("history") or [])
            if reply:
                return jsonify({"reply": reply, "source": "openrouter"})
        except Exception as exc:  # network / key / quota problem -> fall back
            app.logger.warning("OpenRouter call failed, using rules: %s", exc)
        return jsonify({"reply": rule_answer(msg, rows, hist), "source": "rules"})