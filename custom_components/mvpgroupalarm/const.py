"""Constants for the GroupAlarm integration."""
from datetime import timedelta

DOMAIN = "mvpgroupalarm"

DEFAULT_NAME = "mvpGroupAlarm.com"
DEFAULT_SHORT_NAME = "mvpGroupAlarm"

ATTR_NAME = "state"
ATTR_LATEST_UPDATE = "latest_update_utc"
GROUPALARM_DATA = "groupalarm_data"
GROUPALARM_COORDINATOR = "groupalarm_coordinator"
GROUPALARM_NAME = "groupalarm_name"

DEFAULT_TIMEOUT = 10
GROUPALARM_URL = "https://app.groupalarm.com/api/v1"


DEFAULT_SCAN_INTERVAL = timedelta(minutes=1)
