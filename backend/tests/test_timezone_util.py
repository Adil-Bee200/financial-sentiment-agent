from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.timezone_util import calendar_day_bounds, now, to_local_date


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
