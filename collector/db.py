"""
Database schema and write functions.
Two tables: tfl_line_status and rtt_departures.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

log = logging.getLogger(__name__)


def get_connection(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # safe for concurrent reads
    return conn


def initialise(db_path: str) -> None:
    """Create tables if they don't exist."""
    conn = get_connection(db_path)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tfl_line_status (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                collected_at        TEXT NOT NULL,
                line_id             TEXT NOT NULL,
                line_name           TEXT NOT NULL,
                status_severity     INTEGER,
                status_description  TEXT,
                disruption_reason   TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tfl_collected_at
            ON tfl_line_status (collected_at)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tfl_line_id
            ON tfl_line_status (line_id)
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS rtt_departures (
                id                        INTEGER PRIMARY KEY AUTOINCREMENT,
                collected_at              TEXT NOT NULL,
                station_crs               TEXT NOT NULL,
                station_name              TEXT NOT NULL,
                service_uid               TEXT,
                run_date                  TEXT,
                operator                  TEXT,
                origin                    TEXT,
                destination               TEXT,
                booked_departure          TEXT,
                realtime_departure        TEXT,
                realtime_departure_actual INTEGER,  -- 1 if observed, 0 if predicted
                delay_minutes             INTEGER   -- NULL if not calculable
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_rtt_collected_at
            ON rtt_departures (collected_at)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_rtt_station_crs
            ON rtt_departures (station_crs)
        """)
    conn.close()
    log.info("Database initialised at %s", db_path)


def write_tfl_statuses(db_path: str, statuses: list[dict]) -> None:
    """Insert a batch of TfL line status records."""
    if not statuses:
        return
    conn = get_connection(db_path)
    with conn:
        conn.executemany("""
            INSERT INTO tfl_line_status
                (collected_at, line_id, line_name, status_severity,
                 status_description, disruption_reason)
            VALUES
                (:collected_at, :line_id, :line_name, :status_severity,
                 :status_description, :disruption_reason)
        """, statuses)
    conn.close()
    log.debug("Wrote %d TfL status records", len(statuses))


def write_rtt_departures(db_path: str, departures: list[dict]) -> None:
    """Insert a batch of RTT departure records."""
    if not departures:
        return
    conn = get_connection(db_path)
    with conn:
        conn.executemany("""
            INSERT INTO rtt_departures
                (collected_at, station_crs, station_name, service_uid,
                 run_date, operator, origin, destination,
                 booked_departure, realtime_departure,
                 realtime_departure_actual, delay_minutes)
            VALUES
                (:collected_at, :station_crs, :station_name, :service_uid,
                 :run_date, :operator, :origin, :destination,
                 :booked_departure, :realtime_departure,
                 :realtime_departure_actual, :delay_minutes)
        """, departures)
    conn.close()
    log.debug("Wrote %d RTT departure records", len(departures))
