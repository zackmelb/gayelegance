# TramTracker QR notifier

Turns a TramTracker QR code link (like `https://tramtracker.com.au/QRCode/pid.html#pid-page?tid=4151`)
into Telegram notifications when a tram is about to arrive at that stop.

The `tid` in the QR link is the stop/platform ID. `tram_notifier.py` polls
TramTracker's `GetNextPredictionsForStop` endpoint for that stop and messages
a Telegram bot whenever a tram is due within a configurable number of minutes.

## Setup

```bash
pip install -r requirements.txt
```

### Create a Telegram bot and get your chat ID

1. In Telegram, message **[@BotFather](https://t.me/BotFather)** → send `/newbot`
   → follow the prompts (pick a name and a unique username ending in `bot`).
   BotFather replies with a **token** like `123456789:ABCdefGhIJKlmNoPQRstuVwxyz`
   — this is your `TELEGRAM_BOT_TOKEN`.
2. Open a chat with your new bot and send it any message (e.g. "hi") so it
   knows about you — bots can't message you first.
3. Message **[@userinfobot](https://t.me/userinfobot)** to get your numeric
   **chat ID** — this is your `TELEGRAM_CHAT_ID`.

## Run

```bash
export TRAM_STOP_NO=4151              # the "tid" from the QR code URL
export TRAM_ROUTE_NO=0                # 0 = any route through this stop
export TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVwxyz
export TELEGRAM_CHAT_ID=987654321
export NOTIFY_THRESHOLD=5             # notify when a tram is this many minutes away
export POLL_SECONDS=60

python3 tram_notifier.py
```

You'll get a Telegram message such as "🚊 Route 96 to St Kilda Beach arrives
in 4 min" the first time a tram crosses the threshold, and won't be
re-notified for the same tram once it's been flagged.

## Notes / caveats

- `GetNextPredictionsForStop.ashx` is TramTracker's legacy, undocumented JSON
  endpoint (no API key required). It has been used by community projects for
  years but could change or be retired without notice — if it stops responding,
  the documented alternative is Public Transport Victoria's official
  [Timetable API](https://timetableapi.ptv.vic.gov.au/swagger/ui/index), which
  requires registering for a free developer key and signing requests.
- To watch a different stop, scan its QR code (or look at the platform sign)
  and use the number after `tid=` as `TRAM_STOP_NO`.
- Keep your bot token secret — anyone with it can send messages as your bot.
- For "always on" notifications, run this as a background service (systemd unit,
  cron `@reboot`, Docker container, etc.) on something that's always powered on
  (a Raspberry Pi, home server, or small cloud VM), since a phone can't host a
  long-running background poller. The Telegram app on your phone is just where
  the notifications arrive.
