"""
Deliverable 3: Seaborn charts.

Each function takes a list of weather records (dicts from Firestore) and
returns a PNG image as an in-memory buffer, ready to send from Flask.
"""
import io

import matplotlib
matplotlib.use("Agg")  # no GUI window; render straight to memory
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid", context="talk")

MIN_COLOR, MAX_COLOR = "#4C9BE8", "#F26B4E"
SUN_PALETTE = {"Sunny": "#F5B301", "Partly sunny": "#F59E7B", "Mostly cloudy": "#8FA3B8", "Unknown": "#CCCCCC"}


def _to_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _empty(message="No data yet. Run collect_weather.py first."):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=14)
    ax.axis("off")
    return _to_png(fig)


def temperature_chart(rows):
    """Grouped bars: minimum vs maximum temperature for every city."""
    df = pd.DataFrame(rows)
    if df.empty:
        return _empty()

    order = df.sort_values("temp_max_c", ascending=False)["city"].tolist()
    long = df.melt(id_vars="city", value_vars=["temp_min_c", "temp_max_c"],
                   var_name="Type", value_name="temp")
    long["Type"] = long["Type"].map({"temp_min_c": "Minimum", "temp_max_c": "Maximum"})

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=long, x="city", y="temp", hue="Type", order=order,
                palette={"Minimum": MIN_COLOR, "Maximum": MAX_COLOR}, ax=ax)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.0f°", fontsize=11, padding=2)
    ax.set_title(f"Minimum vs Maximum Temperature ({df['date'].iloc[0]})", pad=15)
    ax.set_xlabel("")
    ax.set_ylabel("Temperature (°C)")
    ax.legend(title="", loc="upper right")
    sns.despine()
    return _to_png(fig)


def sunshine_chart(rows):
    """Bars of sunshine hours per city, coloured by sunshine status."""
    df = pd.DataFrame(rows)
    if df.empty:
        return _empty()

    order = df.sort_values("sunshine_hours", ascending=False)["city"].tolist()
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=df, x="city", y="sunshine_hours", hue="sunshine_status",
                order=order, palette=SUN_PALETTE, dodge=False, ax=ax)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f h", fontsize=11, padding=2)
    ax.set_title("Sunshine Hours Today", pad=15)
    ax.set_xlabel("")
    ax.set_ylabel("Hours of sunshine")
    ax.legend(title="Status")
    sns.despine()
    return _to_png(fig)


def conditions_chart(rows):
    """How many cities currently have each weather condition."""
    df = pd.DataFrame(rows)
    if df.empty:
        return _empty()

    order = df["condition"].value_counts().index.tolist()
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.countplot(data=df, y="condition", order=order, hue="condition",
                  palette="viridis", legend=False, ax=ax)
    ax.set_title("Current Weather Conditions Across Cities", pad=15)
    ax.set_xlabel("Number of cities")
    ax.set_ylabel("")
    ax.xaxis.get_major_locator().set_params(integer=True)
    sns.despine()
    return _to_png(fig)


def trend_chart(history_rows):
    """Maximum temperature over the days collected, one line per city."""
    df = pd.DataFrame(history_rows)
    if df.empty:
        return _empty()

    df["date"] = pd.to_datetime(df["date"])
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(data=df, x="date", y="temp_max_c", hue="city",
                 marker="o", linewidth=2.5, ax=ax)
    ax.set_title("Maximum Temperature Trend", pad=15)
    ax.set_xlabel("")
    ax.set_ylabel("Max temperature (°C)")
    ax.legend(title="", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.autofmt_xdate()
    sns.despine()
    return _to_png(fig)
