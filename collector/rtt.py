"""
Realtime Trains departures poller.
Fetches current departures for each configured station and returns
a list of records ready for db.write_rtt_departures().
"""

import logging
import os
from datetime import datetime, timezone

import httpx

from config import RTT_BASE_URL, RTT_STATIONS

log = logging.getLogger(__name__)


def _auth() -> tuple[str, str]:
    return (
        os.environ.get("RTT_USER", ""),
        os.environ.get("RTT_PASS", ""),
    )


def _parse_hhmm(hhmm: str | None) -> int | None:
    """
    Convert a 4-digit HHMM string to minutes since midnight.
    Returns None if input is absent or malformed.
    """
    if not hhmm or len(hhmm) != 4:
        return None
    try:
        return int(hhmm[:2]) * 60 + int(hhmm[2:])
    except ValueError:
        return None


def _delay_minutes(booked: str | None, realtime: str | None) -> int | None:
    """
    Calculate delay in minutes between booked and realtime departure.
    Returns None if either time is unavailable.
    Handles midnight crossings (e.g. booked 2358, realtime 0002 = +4 min).
    """
    b = _parse_hhmm(booked)
    r = _parse_hhmm(realtime)
    if b is None or r is None:
        return None
    diff = r - b
    # Correct for midnight crossing
    if diff > 720:    # more than 12 hours late — must be day wrap
        diff -= 1440
    elif diff < -720: # more than 12 hours early — must be day wrap
        diff += 1440
    return diff


def fetch_station_departures(crs: str, station_name: str) -> list[dict]:
    """
    Fetch current departures for a single station.
    Returns a list of dicts ready to insert into rtt_departures.
    """
    collected_at = datetime.now(timezone.utc).isoformat()
    url = f"{RTT_BASE_URL}/search/{crs}"

    try:
        response = httpx.get(url, auth=_auth(), timeout=10)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        log.error("RTT API error for %s (%s): %s", station_name, crs, exc)
        return []

    data     = response.json()
    services = data.get("services") or []
    records  = []

    for svc in services:
        loc = svc.get("locationDetail", {})

        booked   = loc.get("gbttBookedDeparture")
        realtime = loc.get("realtimeDeparture")
        actual   = loc.get("realtimeDepartureActual", False)

        # Origin and destination are lists — take first of each
        origin_list = loc.get("origin") or svc.get("origin") or []
        dest_list   = loc.get("destination") or svc.get("destination") or []
        origin      = origin_list[0].get("description", "") if origin_list else ""
        destination = dest_list[0].get("description", "")   if dest_list  else ""

        records.append({
            "collected_at":               collected_at,
            "station_crs":                crs,
            "station_name":               station_name,
            "service_uid":                svc.get("serviceUid"),
            "run_date":                   svc.get("runDate"),
            "operator":                   svc.get("atocName"),
            "origin":                     origin,
            "destination":                destination,
            "booked_departure":           booked,
            "realtime_departure":         realtime,
            "realtime_departure_actual":  1 if actual else 0,
            "delay_minutes":              _delay_minutes(booked, realtime),
        })

    log.info("Fetched %d departures for %s (%s)", len(records), station_name, crs)
    return records


def fetch_all_stations() -> list[dict]:
    """Fetch departures for all configured stations."""
    all_records = []
    for crs, name in RTT_STATIONS.items():
        all_records.extend(fetch_station_departures(crs, name))
    return all_records
