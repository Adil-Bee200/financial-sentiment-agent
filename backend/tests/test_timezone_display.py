from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.timezone_util import (
    format_analysis_date_label,
    format_display_datetime_et,
    is_today_local,
)


class TestTimezoneDisplayHelpers:
    def test_format_analysis_date_label(self):
        assert format_analysis_date_label(date(2026, 6, 17)) == "Wed, Jun 17"

    def test_format_display_datetime_et(self):
        value = datetime(2026, 6, 16, 21, 48, tzinfo=ZoneInfo("UTC"))
        assert format_display_datetime_et(value) == "Jun 16, 5:48 PM ET"

    def test_is_today_local(self):
        today = datetime.now(ZoneInfo("America/New_York")).date()
        assert is_today_local(today) is True
        assert is_today_local(date(2000, 1, 1)) is False
