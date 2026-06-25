"""
Configuration — stations, lines, polling intervals.
Secrets (TFL_API_KEY, RTT_USER, RTT_PASS) come from environment variables.
"""

# RTT stations to poll (CRS code -> display name)
RTT_STATIONS = {
    "SRS": "Selhurst",
    "NWD": "Norwood Junction",
    "VIC": "London Victoria",
    "CLJ": "Clapham Junction",
    "LBG": "London Bridge",
    "ECR": "East Croydon",
    "BFR": "Blackfriars",
    "CTK": "City Thameslink",
    "ZFD": "Farringdon",
    "STP": "St Pancras International",
}

# TfL lines to poll for status
TFL_LINES = [
    "northern",
    "victoria",
    "jubilee",
    "bakerloo",
    "elizabeth",
    "london-overground",
]

# Polling intervals in seconds
TFL_STATUS_INTERVAL  = 120   # every 2 minutes
RTT_DEPARTURES_INTERVAL = 300  # every 5 minutes

# Only collect during operating hours (avoids overnight engineering window noise)
OPERATING_HOURS_START = 6   # 06:00
OPERATING_HOURS_END   = 23  # 23:00

# Database path — override with DB_PATH env var
import os
DB_PATH = os.environ.get("DB_PATH", "/data/tfl-delay-collector/delays.db")

# API base URLs
TFL_BASE_URL = "https://api.tfl.gov.uk"
RTT_BASE_URL = "https://api.rtt.io/api/v1/json"
