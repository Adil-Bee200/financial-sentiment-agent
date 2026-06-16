from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.timezone_util import (
    calendar_day_bounds,
    format_newsapi_datetime,
    now,
    parse_external_datetime,
    to_app_timezone,
    to_local_date,
    to_utc,
)


class TestTimezoneUtil:
    def test_calendar_day_bounds_eastern(self):
        eastern = ZoneInfo("America/New_York")
        # 2026-06-13 02:00 UTC = 2026-06-12 22:00 EDT (still previous Eastern day)
        as_of = datetime(2026, 6, 13, 2, 0, tzinfo=ZoneInfo("UTC"))
        start, end = calendar_day_bounds(as_of)

        assert start.tzinfo == eastern
        assert start == datetime(2026, 6, 12, 0, 0, tzinfo=eastern)
        assert end == datetime(2026, 6, 13, 0, 0, tzinfo=eastern)

    def test_to_local_date_uses_eastern_calendar(self):
        utc_late = datetime(2026, 6, 13, 3, 0, tzinfo=ZoneInfo("UTC"))
        assert to_local_date(utc_late).isoformat() == "2026-06-12"

    def test_now_returns_aware_eastern(self):
        current = now()
        assert current.tzinfo is not None
        assert str(current.tzinfo) in {"America/New_York", "EDT", "EST"}

    def test_parse_external_datetime_converts_utc_to_eastern(self):
        # 18:00 UTC = 14:00 EDT on same calendar day in summer
        parsed = parse_external_datetime("2026-06-13T18:00:00Z")
        assert parsed.hour == 14
        assert parsed.tzinfo == ZoneInfo("America/New_York")

    def test_to_app_timezone_from_utc(self):
        utc = datetime(2026, 1, 15, 17, 0, tzinfo=ZoneInfo("UTC"))
        eastern = to_app_timezone(utc)
        assert eastern.hour == 12  # EST (UTC-5) in January

    def test_format_newsapi_datetime_outputs_utc(self):
        eastern = datetime(2026, 1, 15, 12, 0, tzinfo=ZoneInfo("America/New_York"))
        assert format_newsapi_datetime(eastern) == "2026-01-15T17:00:00"

    def test_to_utc_from_eastern(self):
        eastern = datetime(2026, 1, 15, 12, 0, tzinfo=ZoneInfo("America/New_York"))
        assert to_utc(eastern).hour == 17
