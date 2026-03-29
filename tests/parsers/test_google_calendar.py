"""Tests for Google Calendar iCal parser."""

from datetime import datetime

import aiohttp
import pytest
from aioresponses import aioresponses
from freezegun import freeze_time

from around_the_grounds.models import Brewery
from around_the_grounds.parsers.google_calendar import GoogleCalendarParser

ICAL_FIXTURE = """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Google Inc//EN
X-WR-TIMEZONE:America/Los_Angeles
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260402
DTEND;VALUE=DATE:20260403
SUMMARY:LIVE MUSIC: Test Band
END:VEVENT
BEGIN:VEVENT
DTSTART;TZID=America/Los_Angeles:20260401T183000
DTEND;TZID=America/Los_Angeles:20260401T200000
RRULE:FREQ=WEEKLY;BYDAY=WE
SUMMARY:Trivia Night
END:VEVENT
BEGIN:VEVENT
DTSTART;TZID=America/Los_Angeles:20260401T173000
DTEND;TZID=America/Los_Angeles:20260401T190000
RRULE:FREQ=WEEKLY;BYDAY=MO
SUMMARY:Running Club
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20250101
DTEND;VALUE=DATE:20250102
SUMMARY:Past Event
END:VEVENT
BEGIN:VEVENT
DTSTART:20260404T010000Z
DTEND:20260404T030000Z
SUMMARY:UTC Timed Event
END:VEVENT
END:VCALENDAR
"""


class TestGoogleCalendarParser:
    @pytest.fixture
    def brewery(self) -> Brewery:
        return Brewery(
            key="broadview-taphouse-events",
            name="Broadview Tap House",
            url="https://calendar.google.com/calendar/ical/bvtaphouseevents%40gmail.com/public/basic.ics",
            website_url="https://www.broadviewtaphouse.com/event-calendar",
            parser_config={"note": "Google Calendar iCal feed"},
        )

    @pytest.fixture
    def parser(self, brewery: Brewery) -> GoogleCalendarParser:
        return GoogleCalendarParser(brewery)

    @pytest.mark.asyncio
    @freeze_time("2026-03-30")
    async def test_parse_date_only_event(self, parser: GoogleCalendarParser) -> None:
        """Date-only events are parsed with no start/end time."""
        with aioresponses() as m:
            m.get(parser.brewery.url, status=200, body=ICAL_FIXTURE)
            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)

        live_music = next(e for e in events if "Test Band" in e.food_truck_name)
        assert live_music.date == datetime(2026, 4, 2)
        assert live_music.start_time is None
        assert live_music.end_time is None
        assert live_music.category == "live-music"

    @pytest.mark.asyncio
    @freeze_time("2026-03-30")
    async def test_recurring_weekly_expanded(self, parser: GoogleCalendarParser) -> None:
        """Weekly recurring events are expanded into multiple occurrences."""
        with aioresponses() as m:
            m.get(parser.brewery.url, status=200, body=ICAL_FIXTURE)
            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)

        trivia = [e for e in events if "Trivia" in e.food_truck_name]
        assert len(trivia) >= 1
        assert all(e.category == "trivia" for e in trivia)
        # Each occurrence should be a Wednesday
        assert all(e.date.weekday() == 2 for e in trivia)
        # Should have start/end times from the template
        assert all(e.start_time is not None for e in trivia)

    @pytest.mark.asyncio
    @freeze_time("2026-03-30")
    async def test_past_event_filtered(self, parser: GoogleCalendarParser) -> None:
        """Events in the past are not returned."""
        with aioresponses() as m:
            m.get(parser.brewery.url, status=200, body=ICAL_FIXTURE)
            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)

        names = [e.food_truck_name for e in events]
        assert "Past Event" not in names

    @pytest.mark.asyncio
    @freeze_time("2026-03-30")
    async def test_utc_timed_event(self, parser: GoogleCalendarParser) -> None:
        """UTC datetime events are converted to Pacific time."""
        with aioresponses() as m:
            m.get(parser.brewery.url, status=200, body=ICAL_FIXTURE)
            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)

        utc_event = next(e for e in events if "UTC Timed Event" in e.food_truck_name)
        # 2026-04-04T01:00:00Z = 2026-04-03T18:00:00 PDT
        assert utc_event.date == datetime(2026, 4, 3)
        assert utc_event.start_time is not None
        assert utc_event.start_time.hour == 18

    @pytest.mark.asyncio
    @freeze_time("2026-03-30")
    async def test_category_detection(self, parser: GoogleCalendarParser) -> None:
        """Event categories are detected from SUMMARY keywords."""
        with aioresponses() as m:
            m.get(parser.brewery.url, status=200, body=ICAL_FIXTURE)
            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)

        run = next(e for e in events if "Running" in e.food_truck_name)
        assert run.category == "community"

    @pytest.mark.asyncio
    async def test_http_error_returns_empty(self, parser: GoogleCalendarParser) -> None:
        """HTTP errors return an empty list gracefully."""
        with aioresponses() as m:
            m.get(parser.brewery.url, status=500)
            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)
        assert events == []
