"""
TfL line status poller.
Fetches current status for each configured line and returns
a list of records ready for db.write_tfl_statuses().
"""

import logging
import os
from datetime import datetime, timezone

import httpx

from config import TFL_BASE_URL, TFL_LINES

log = logging.getLogger(__name__)


def _api_key() -> dict:
    key = os.environ.get("TFL_API_KEY", "")
    return {"app_key": key} if key else {}


def fetch_line_statuses() -> list[dict]:
    """
    Fetch current status for all configured TfL lines.
    Returns a list of dicts ready to insert into tfl_line_status.
    """
    collected_at = datetime.now(timezone.utc).isoformat()
    line_ids = ",".join(TFL_LINES)
    url = f"{TFL_BASE_URL}/Line/{line_ids}/Status"

    try:
        response = httpx.get(url, params=_api_key(), timeout=10)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        log.error("TfL API error: %s", exc)
        return []

    records = []
    for line in response.json():
        line_id   = line.get("id", "")
        line_name = line.get("name", "")

        for status in line.get("lineStatuses", []):
            severity    = status.get("statusSeverity")
            description = status.get("statusSeverityDescription", "")
            reason      = status.get("reason", "") or ""

            # Clean up the reason text — TfL prepends "TUBE: Line Name: " etc.
            if reason and ":" in reason:
                parts = reason.split(":", 2)
                reason = parts[-1].strip() if len(parts) >= 2 else reason

            records.append({
                "collected_at":       collected_at,
                "line_id":            line_id,
                "line_name":          line_name,
                "status_severity":    severity,
                "status_description": description,
                "disruption_reason":  reason or None,
            })

    log.info("Fetched TfL status for %d lines (%d status records)",
             len(response.json()), len(records))
    return records
