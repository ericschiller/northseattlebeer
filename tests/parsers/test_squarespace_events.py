"""Tests for Squarespace Events parser."""

import re
from datetime import datetime
from typing import Any, Dict

import aiohttp
import pytest
from aioresponses import aioresponses
from freezegun import freeze_time

from around_the_grounds.models import Brewery
from around_the_grounds.parsers.squarespace_events import SquarespaceEventsParser


class TestSquarespaceEventsParser:
    """Test the SquarespaceEventsParser class."""

    @pytest.fixture
    def brewery(self) -> Brewery:
        """Create a test brewery for Ridgecrest Pub."""
        return Brewery(
            key="ridgecrest-pub",
            name="Ridgecrest Public House",
            url="https://www.ridgecrest.pub/foodtruckcalendarfunctional",
            parser_config={
                "note": "Squarespace events collection JSON",
                "api_type": "squarespace_events",
                "exclude_patterns": ["Trivia", "Knit Nite"]
            },
        )

    @pytest.fixture
    def parser(self, brewery: Brewery) -> SquarespaceEventsParser:
        """Create a parser instance."""
        return SquarespaceEventsParser(brewery)

    @pytest.fixture
    def sample_json_response(self) -> Dict[str, Any]:
        """Sample JSON response from Squarespace Events collection."""
        return {
            "items": [
                {
                    "title": "Kathmandu MoMoCha",
                    "startDate": 1754092800000,  # 2025-08-01 17:00:00 PDT (approx)
                    "endDate": 1754107200000,    # 2025-08-01 21:00:00 PDT (approx)
                },
                {
                    "title": "Ridgecrest Knit Nite",
                    "startDate": 1754179200000,
                    "endDate": 1754193600000,
                },
                {
                    "title": "Oskars Pizza",
                    "startDate": 1754265600000,
                    "endDate": 1754280000000,
                },
                {
                    "title": "Trivia at Drumlin",
                    "startDate": 1754352000000,
                    "endDate": 1754366400000,
                }
            ]
        }

    @pytest.mark.asyncio
    @freeze_time("2025-07-01")
    async def test_parse_squarespace_json(
        self, parser: SquarespaceEventsParser, sample_json_response: Dict[str, Any]
    ) -> None:
        """Test parsing Squarespace JSON data successfully."""
        with aioresponses() as m:
            # Mock the ?format=json request
            url_pattern = re.compile(re.escape(parser.brewery.url) + r".*format=json.*")
            m.get(url_pattern, status=200, payload=sample_json_response)

            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)

                # Should have 2 events (Kathmandu MoMoCha and Oskars Pizza)
                # Knit Nite and Trivia should be excluded
                assert len(events) == 2
                
                titles = [e.food_truck_name for e in events]
                assert "Kathmandu MoMoCha" in titles
                assert "Oskars Pizza" in titles
                assert "Ridgecrest Knit Nite" not in titles
                assert "Trivia at Drumlin" not in titles

                # Check event details
                event = next(e for e in events if e.food_truck_name == "Kathmandu MoMoCha")
                assert event.brewery_key == "ridgecrest-pub"
                assert event.date is not None
                assert isinstance(event.date, datetime)

    @pytest.mark.asyncio
    async def test_parse_empty_items(self, parser: SquarespaceEventsParser) -> None:
        """Test parsing when no items are returned."""
        with aioresponses() as m:
            url_pattern = re.compile(re.escape(parser.brewery.url) + r".*")
            m.get(url_pattern, status=200, payload={"items": []})

            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)
                assert len(events) == 0

    @pytest.mark.asyncio
    async def test_parse_error_response(self, parser: SquarespaceEventsParser) -> None:
        """Test handling of HTTP error response."""
        with aioresponses() as m:
            url_pattern = re.compile(re.escape(parser.brewery.url) + r".*")
            m.get(url_pattern, status=500)

            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)
                assert len(events) == 0  # Should handle gracefully and return empty list
