"""
Deliverable 1 (scheduling): keep the database up to date.

Collects immediately, then once per interval. Used by the `collector`
service in docker-compose, or run it yourself:  python scheduler.py

Interval comes from COLLECT_INTERVAL_SECONDS (default 3600).
"""
import os
import time

import collect_weather


def run():
    interval = max(60, int(os.getenv("COLLECT_INTERVAL_SECONDS", "3600")))
    while True:
        started = time.time()
        try:
            collect_weather.main()
        except Exception as exc:
            print(f"[scheduler] collection failed: {exc}")
        time.sleep(max(1, interval - (time.time() - started)))


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        pass
