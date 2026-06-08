# TramTracker QR notifier

Turns a TramTracker QR code link (like `https://tramtracker.com.au/QRCode/pid.html#pid-page?tid=4151`)
into push notifications when a tram is about to arrive at that stop.

The `tid` in the QR link is the stop/platform ID. `tram_notifier.py` polls
TramTracker's `GetNextPredictionsForStop` endpoint for that stop and sends a
push notification via [ntfy.sh](https://ntfy.sh) whenever a tram is due within
a configurable number of minutes.

## Setup

```bash
pip install -r requirements.txt
```

Pick an ntfy topic (any unguessable string works as a free, unauthenticated
"channel") and subscribe to it on your phone via the [ntfy app](https://ntfy.sh/)
or in a browser at `https://ntfy.sh/<your-topic>`.

## Run

```bash
export TRAM_STOP_NO=4151        # the "tid" from the QR code URL
export TRAM_ROUTE_NO=0          # 0 = any route through this stop
export NTFY_TOPIC=your-unguessable-topic
export NOTIFY_THRESHOLD=5       # notify when a tram is this many minutes away
export POLL_SECONDS=60

python3 tram_notifier.py
```

You'll get a push notification such as "Route 96 to St Kilda Beach arrives in
4 min" the first time a tram crosses the threshold, and won't be re-notified
for the same tram once it's been flagged.

## Notes / caveats

- `GetNextPredictionsForStop.ashx` is TramTracker's legacy, undocumented JSON
  endpoint (no API key required). It has been used by community projects for
  years but could change or be retired without notice — if it stops responding,
  the documented alternative is Public Transport Victoria's official
  [Timetable API](https://timetableapi.ptv.vic.gov.au/swagger/ui/index), which
  requires registering for a free developer key and signing requests.
- To watch a different stop, scan its QR code (or look at the platform sign)
  and use the number after `tid=` as `TRAM_STOP_NO`.
- For "always on" notifications, run this as a background service (systemd unit,
  cron `@reboot`, Docker container, etc.) rather than in a foreground terminal.
