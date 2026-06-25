"""
Main scheduler — runs both pollers on independent intervals.
Uses a simple sleep-based approach rather than a full scheduler
library, keeping dependencies minimal.
"""

import logging
import time
from datetime import datetime, timezone

from config import (
    DB_PATH,
    TFL_STATUS_INTERVAL,
    RTT_DEPARTURES_INTERVAL,
    OPERATING_HOURS_START,
    OPERATING_HOURS_END,
)
from collector.db  import initialise, write_tfl_statuses, write_rtt_departures
from collector.tfl import fetch_line_statuses
from collector.rtt import fetch_all_stations

log = logging.getLogger(__name__)


def _within_operating_hours() -> bool:
    hour = datetime.now().hour
    return OPERATING_HOURS_START <= hour < OPERATING_HOURS_END


def run() -> None:
    """
    Run both pollers indefinitely.
    Each poller tracks its own last-run time and fires when its
    interval has elapsed, provided we're within operating hours.
    """
    log.info("Initialising database at %s", DB_PATH)
    initialise(DB_PATH)

    last_tfl = 0.0
    last_rtt = 0.0

    log.info(
        "Collector started. TfL interval=%ds, RTT interval=%ds, "
        "operating hours=%02d:00–%02d:00",
        TFL_STATUS_INTERVAL, RTT_DEPARTURES_INTERVAL,
        OPERATING_HOURS_START, OPERATING_HOURS_END,
    )

    while True:
        now = time.monotonic()

        if not _within_operating_hours():
            log.debug("Outside operating hours — sleeping 60s")
            time.sleep(60)
            continue

        # TfL line status poll
        if now - last_tfl >= TFL_STATUS_INTERVAL:
            try:
                statuses = fetch_line_statuses()
                write_tfl_statuses(DB_PATH, statuses)
                last_tfl = time.monotonic()
            except Exception:
                log.exception("Unhandled error in TfL poller")

        # RTT departures poll
        if now - last_rtt >= RTT_DEPARTURES_INTERVAL:
            try:
                departures = fetch_all_stations()
                write_rtt_departures(DB_PATH, departures)
                last_rtt = time.monotonic()
            except Exception:
                log.exception("Unhandled error in RTT poller")

        time.sleep(10)  # check every 10s whether a poller is due
