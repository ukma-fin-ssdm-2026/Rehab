"""One calendar day for the service, independent of the host timezone.

AI-GENERATED START: prepared with ChatGPT; UTC/Kyiv boundary tested.
"""

import datetime as dt
from zoneinfo import ZoneInfo

BUSINESS_TIMEZONE = ZoneInfo("Europe/Kyiv")


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def today_local() -> dt.date:
    return utc_now().astimezone(BUSINESS_TIMEZONE).date()


# AI-GENERATED END
