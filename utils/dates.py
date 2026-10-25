from datetime import date, datetime
from zoneinfo import ZoneInfo

# The app is built for customers in India. Hosted servers run on UTC,
# so "today" must be worked out in Indian time, not server time.
APP_TIMEZONE = ZoneInfo("Asia/Kolkata")


def today_local():
    """Today's date in Indian Standard Time."""
    return datetime.now(APP_TIMEZONE).date()