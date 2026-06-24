"""Constants for the Fur Affinity Status integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "furaffinity"

DEFAULT_NAME = "Fur Affinity Status"

ATTRIBUTION = "Data provided by status.furaffinity.net"

CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 5

API_URL = "https://status.furaffinity.net/api/v1/status/"

MIN_SCAN_INTERVAL = 1
MAX_SCAN_INTERVAL = 60

UPDATE_INTERVAL = timedelta(seconds=300)

STATUS_UP = "up"
STATUS_DOWN = "down"
STATUS_PAUSED = "paused"

OVERALL_STATUS_MAP = {
    "up": "operational",
    "down": "down",
    "paused": "paused",
    "investigating": "investigating",
    "identified": "identified",
    "monitoring": "monitoring",
    "resolved": "resolved",
}

ALERT_TYPE_INFO = "info"
ALERT_TYPE_WARNING = "warning"
ALERT_TYPE_DANGER = "danger"
