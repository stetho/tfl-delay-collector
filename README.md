# tfl-delay-collector

A lightweight data collector that polls the TfL Unified API and the Realtime
Trains API on a schedule, storing delay data to SQLite for later analysis.

Part of the [tfl-delay-analysis](https://github.com/stetho/tfl-delay-analysis)
project — this service collects the data; the analysis repo is where the
interesting questions get asked.

## What it collects

**TfL line status** (every 2 minutes, 06:00–23:00)
Line status severity and disruption reason for: Northern, Victoria, Jubilee,
Bakerloo, Elizabeth line, London Overground.

**RTT departures** (every 5 minutes, 06:00–23:00)
Booked vs actual departure times for all services at:
Selhurst, Norwood Junction, London Victoria, Clapham Junction, London Bridge,
East Croydon, Blackfriars, City Thameslink, Farringdon, St Pancras.

Delay in minutes is derived from the difference between `gbttBookedDeparture`
and `realtimeDeparture` in the RTT response.

## Setup

### Credentials

Register for a TfL API key at [api-portal.tfl.gov.uk](https://api-portal.tfl.gov.uk).
Use your existing Realtime Trains API credentials.

Create a `.env` file (never committed):
```
TFL_API_KEY=your_primary_key_here
RTT_USER=your_rtt_username
RTT_PASS=your_rtt_password
```

### Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
TFL_API_KEY=... RTT_USER=... RTT_PASS=... python main.py
```

### Docker (production on proliant1)

```bash
docker compose --env-file .env up -d
```

The database is written to a named Docker volume (`tfl-delay-data`) at
`/data/delays.db` inside the container.

## Database schema

```sql
tfl_line_status (
    collected_at, line_id, line_name,
    status_severity, status_description, disruption_reason
)

rtt_departures (
    collected_at, station_crs, station_name,
    service_uid, run_date, operator, origin, destination,
    booked_departure, realtime_departure,
    realtime_departure_actual, delay_minutes
)
```

`status_severity` follows TfL's scale: 0 = Good service, 6 = Minor delays,
10 = Severe delays, 20 = Part suspended, 30 = Suspended.

`realtime_departure_actual` is 1 if the time is observed, 0 if predicted.
For analysis, filter to `realtime_departure_actual = 1` for real delay data.
