#!/usr/bin/env python3
"""Poll TramTracker for a stop and push an ntfy.sh notification when a tram is due soon.

Configuration via environment variables:
    TRAM_STOP_NO      Stop/platform ID, e.g. the "tid" from a QR code link (default: 4151)
    TRAM_ROUTE_NO     Route number to filter on, 0 = all routes (default: 0)
    NTFY_TOPIC        ntfy.sh topic to publish to (required)
    NTFY_SERVER       ntfy server base URL (default: https://ntfy.sh)
    NOTIFY_THRESHOLD  Notify when a tram is within this many minutes (default: 5)
    POLL_SECONDS      How often to check for predictions (default: 60)
"""
import os
import time
from datetime import datetime, timezone

import requests

PREDICTIONS_URL = "https://www.tramtracker.com.au/Controllers/GetNextPredictionsForStop.ashx"


def fetch_predictions(stop_no: int, route_no: int) -> list[dict]:
    response = requests.get(
        PREDICTIONS_URL,
        params={"stopNo": stop_no, "routeNo": route_no, "isLowFloor": "false"},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("responseObject") or []


def minutes_until(predicted_arrival: dict) -> float | None:
    raw = predicted_arrival.get("PredictedArrivalDateTime")
    if not raw:
        return None
    # TramTracker returns .NET JSON dates like "/Date(1717828800000+1000)/"
    millis = int(raw.split("(")[1].split("+")[0].split("-")[0])
    arrival = datetime.fromtimestamp(millis / 1000, tz=timezone.utc)
    delta = arrival - datetime.now(tz=timezone.utc)
    return delta.total_seconds() / 60


def notify(server: str, topic: str, title: str, message: str) -> None:
    requests.post(f"{server.rstrip('/')}/{topic}", data=message.encode("utf-8"),
                  headers={"Title": title}, timeout=10)


def main() -> None:
    stop_no = int(os.environ.get("TRAM_STOP_NO", "4151"))
    route_no = int(os.environ.get("TRAM_ROUTE_NO", "0"))
    topic = os.environ["NTFY_TOPIC"]
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
    threshold = float(os.environ.get("NOTIFY_THRESHOLD", "5"))
    poll_seconds = int(os.environ.get("POLL_SECONDS", "60"))

    already_notified: set[str] = set()

    print(f"Watching stop {stop_no} (route {route_no or 'any'}), "
          f"notifying via {server}/{topic} when a tram is within {threshold:.0f} min")

    while True:
        try:
            predictions = fetch_predictions(stop_no, route_no)
            current_keys = set()

            for prediction in predictions:
                key = f"{prediction.get('TripID')}-{prediction.get('PredictedArrivalDateTime')}"
                current_keys.add(key)

                eta = minutes_until(prediction)
                if eta is None or eta < 0 or eta > threshold or key in already_notified:
                    continue
                already_notified.add(key)

                route = prediction.get("RouteNo", "?")
                destination = prediction.get("Destination", "Unknown destination")
                notify(server, topic, "Tram approaching",
                       f"Route {route} to {destination} arrives in {eta:.0f} min")
                print(f"Notified: route {route} to {destination} in {eta:.1f} min")

            # Forget trams that have dropped off the predictions list (departed/arrived)
            already_notified &= current_keys
        except requests.RequestException as exc:
            print(f"Fetch failed: {exc}")

        time.sleep(poll_seconds)


if __name__ == "__main__":
    main()
