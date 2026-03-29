"""Tests for Chuck's Greenwood parser."""

from pathlib import Path
from datetime import datetime

import aiohttp
import pytest
from aioresponses import aioresponses
from freezegun import freeze_time

from around_the_grounds.models import Brewery
from around_the_grounds.parsers.chucks_greenwood import ChucksGreenwoodParser


class TestChucksGreenwoodParser:
    """Test the ChucksGreenwoodParser class."""

    @pytest.fixture
    def brewery(self) -> Brewery:
        """Create a test brewery for Chuck's Greenwood."""
        return Brewery(
            key="chucks-greenwood",
            name="Chuck's Hop Shop Greenwood",
            url="https://docs.google.com/spreadsheets/d/e/2PACX-1vS8BmXLSrsUVJ1x_x8FslWooOXRLeEJV-Jq5NzhfUCI9TtO-qXr0ey2BzY8KI-GflT7ekl5015XX3uj/pub?gid=1143085558&single=true&output=csv",
            parser_config={
                "note": "Google Sheets CSV export with automatic monthly updates",
                "csv_direct": True,
                "event_type_filter": "Food Truck",
            },
        )

    @pytest.fixture
    def parser(self, brewery: Brewery) -> ChucksGreenwoodParser:
        """Create a parser instance."""
        return ChucksGreenwoodParser(brewery)

    @pytest.fixture
    def sample_csv(self, csv_fixtures_dir: Path) -> str:
        """Load sample CSV fixture."""
        fixture_path = csv_fixtures_dir / "chucks_greenwood_sample.csv"
        return fixture_path.read_text()

    @pytest.fixture
    def sample_html(self, html_fixtures_dir: Path) -> str:
        """Load sample HTML fixture."""
        fixture_path = html_fixtures_dir / "chucks_greenwood_sample.html"
        return fixture_path.read_text()

    # SUCCESS CASES

    @pytest.mark.asyncio
    @freeze_time("2025-08-05")  # Use consistent test date
    async def test_parse_sample_csv_data(
        self, parser: ChucksGreenwoodParser, sample_csv: str
    ) -> None:
        """Test parsing the sample CSV data."""
        with aioresponses() as m:
            m.get(parser.brewery.url, status=200, body=sample_csv)

            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)

                # Validate results
                assert len(events) > 0
                assert all(event.brewery_key == "chucks-greenwood" for event in events)
                assert all(
                    event.brewery_name == "Chuck's Hop Shop Greenwood"
                    for event in events
                )
                assert all(event.food_truck_name.strip() != "" for event in events)
                assert all(event.date is not None for event in events)

                # Check specific events from sample data
                event_names = [event.food_truck_name for event in events]
                assert "T'Juana" in event_names  # From "Dinner: T'Juana"
                assert (
                    "Good Morning Tacos" in event_names
                )  # From "Brunch: Good Morning Tacos"
                assert "Tat's Deli" in event_names  # No prefix

                # Verify non-truck events are included but with correct categories
                trivia = next((e for e in events if "Trivia" in e.food_truck_name), None)
                assert trivia is not None
                assert trivia.category == "trivia"

                bingo = next((e for e in events if "Bingo" in e.food_truck_name), None)
                assert bingo is not None
                assert bingo.category == "community"

                # Verify food trucks have food-truck category
                truck = next(e for e in events if e.food_truck_name == "T'Juana")
                assert truck.category == "food-truck"

    @pytest.mark.asyncio
    @freeze_time("2025-08-01")
    async def test_meal_times_and_cleaning(
        self, parser: ChucksGreenwoodParser
    ) -> None:
        """Test that times are correctly assigned and names are cleaned."""
        csv_data = """Greenwood Events & Food Trucks,,,,,,,
Sun,Aug 3,12 AM,to,Sun,Food Truck,Brunch: Good Morning Tacos,Wed,Sun,FALSE,TRUE
Sun,Aug 3,12 AM,to,Sat,Food Truck,Dinner: Georgia's Greek,Sat,Sat,FALSE,TRUE
Mon,Aug 4,12 AM,to,Sat,Food Truck,Tat's Deli,Sun,Sat,FALSE,TRUE"""

        with aioresponses() as m:
            m.get(parser.brewery.url, status=200, body=csv_data)

            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)
                assert len(events) == 3

                # Brunch check
                brunch = next(e for e in events if e.food_truck_name == "Good Morning Tacos")
                assert brunch.start_time.hour == 11
                assert brunch.end_time.hour == 15
                assert brunch.description == "Brunch"

                # Dinner check
                dinner = next(e for e in events if e.food_truck_name == "Georgia's Greek")
                assert dinner.start_time.hour == 17
                assert dinner.end_time.hour == 21
                assert dinner.description == "Dinner"

                # No prefix check (should default to dinner)
                no_prefix = next(e for e in events if e.food_truck_name == "Tat's Deli")
                assert no_prefix.start_time.hour == 17
                assert no_prefix.description is None

    @pytest.mark.asyncio
    @freeze_time("2025-08-05")
    async def test_parse_with_redirect(
        self, parser: ChucksGreenwoodParser, sample_csv: str
    ) -> None:
        """Test parsing with Google CDN redirect."""
        redirect_url = "https://doc-0s-3s-sheets.googleusercontent.com/pub/example/csv"

        with aioresponses() as m:
            # Mock redirect from original URL to CDN
            m.get(parser.brewery.url, status=307, headers={"Location": redirect_url})
            m.get(redirect_url, status=200, body=sample_csv)

            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)
                assert len(events) > 0

    # ERROR HANDLING TESTS

    @pytest.mark.asyncio
    async def test_parse_empty_csv(self, parser: ChucksGreenwoodParser) -> None:
        """Test parsing when CSV is empty."""
        empty_csv = ""

        with aioresponses() as m:
            m.get(parser.brewery.url, status=200, body=empty_csv)

            async with aiohttp.ClientSession() as session:
                with pytest.raises(ValueError, match="Failed to parse CSV data"):
                    await parser.parse(session)

    @pytest.mark.asyncio
    async def test_parse_header_only_csv(self, parser: ChucksGreenwoodParser) -> None:
        """Test parsing when CSV has only headers."""
        header_only_csv = "Greenwood Events & Food Trucks,,,,,,,Date Created,Last Updated,All Day Event,Recurring Event"

        with aioresponses() as m:
            m.get(parser.brewery.url, status=200, body=header_only_csv)

            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)
                assert len(events) == 0

    @pytest.mark.asyncio
    async def test_parse_no_food_truck_events(
        self, parser: ChucksGreenwoodParser
    ) -> None:
        """Test parsing when only non-truck Event rows are present."""
        non_food_truck_csv = """Greenwood Events & Food Trucks,,,,,,,Date Created,Last Updated,All Day Event,Recurring Event
Wed,Aug 6,12 AM,to,Wed,Event,Geeks Who Drink Trivia,Thu,Wed,FALSE,TRUE
Tue,Aug 12,12 AM,to,Tue,Event,Music Bingo,Wed,Tue,FALSE,TRUE"""

        with aioresponses() as m:
            m.get(parser.brewery.url, status=200, body=non_food_truck_csv)

            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)
                # Event rows are now included — trivia and community categories
                assert len(events) == 2
                assert all(e.category in ("trivia", "community") for e in events)

    # VENDOR NAME EXTRACTION TESTS

    def test_extract_vendor_and_meal(
        self, parser: ChucksGreenwoodParser
    ) -> None:
        """Test vendor name and meal type extraction."""
        name, meal = parser._extract_vendor_and_meal("Dinner: T'Juana")
        assert name == "T'Juana"
        assert meal == "dinner"

        name, meal = parser._extract_vendor_and_meal("Brunch: Good Morning Tacos")
        assert name == "Good Morning Tacos"
        assert meal == "brunch"

        name, meal = parser._extract_vendor_and_meal("Tat's Deli")
        assert name == "Tat's Deli"
        assert meal is None

    # DATE PARSING TESTS

    @freeze_time("2025-08-05")
    def test_parse_date_current_year(self, parser: ChucksGreenwoodParser) -> None:
        """Test date parsing for current year."""
        result = parser._parse_date_from_month_date_column("Fri", "Aug 15")
        assert result is not None
        assert result.year == 2025
        assert result.month == 8
        assert result.day == 15

    @freeze_time("2025-12-25")
    def test_parse_date_next_year_rollover(self, parser: ChucksGreenwoodParser) -> None:
        """Test date parsing with year rollover."""
        result = parser._parse_date_from_month_date_column("Wed", "Jan 15")
        assert result is not None
        assert result.year == 2026  # Should be next year
        assert result.month == 1
        assert result.day == 15
