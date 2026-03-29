"""Tests for WA Food Trucks parser."""

from datetime import datetime
from typing import Any, Dict

import aiohttp
import pytest
from aioresponses import aioresponses
from freezegun import freeze_time

from around_the_grounds.models import Brewery
from around_the_grounds.parsers.wa_food_trucks import WaFoodTrucksParser


class TestWaFoodTrucksParser:
    """Test the WaFoodTrucksParser class."""

    @pytest.fixture
    def brewery(self) -> Brewery:
        """Create a test brewery for Shoreline CC."""
        return Brewery(
            key="shoreline-cc",
            name="Shoreline Community College",
            url="https://wafoodtrucks.org/shorelinecc",
            parser_config={
                "note": "WA Food Truck Association Squarespace page with list of dates",
                "api_type": "wa_food_trucks"
            },
        )

    @pytest.fixture
    def parser(self, brewery: Brewery) -> WaFoodTrucksParser:
        """Create a parser instance."""
        return WaFoodTrucksParser(brewery)

    @pytest.fixture
    def sample_json_response(self) -> Dict[str, Any]:
        """Sample JSON response from wafoodtrucks.org."""
        return {
            "mainContent": """
                <div class="sqs-block html-block">
                    <div class="sqs-block-content">
                        <h3>April 2nd - La Costenita Cuisine</h3>
                        <h3>April 6th - Spice Shuttle</h3>
                        <p>May 5th - Taco Cortes</p>
                        <h3>Not a date - Just text</h3>
                    </div>
                </div>
            """
        }

    @pytest.mark.asyncio
    @freeze_time("2026-03-01")
    async def test_parse_wa_food_trucks_html(
        self, parser: WaFoodTrucksParser, sample_json_response: Dict[str, Any]
    ) -> None:
        """Test parsing WA Food Trucks HTML content from JSON successfully."""
        with aioresponses() as m:
            # Mock the ?format=json request
            m.get(re.compile(r".*format=json.*"), status=200, payload=sample_json_response)

            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)

                # Should have 3 events
                assert len(events) == 3
                
                truck_names = [e.food_truck_name for e in events]
                assert "La Costenita Cuisine" in truck_names
                assert "Spice Shuttle" in truck_names
                assert "Taco Cortes" in truck_names

                # Check specific event details
                event = next(e for e in events if e.food_truck_name == "La Costenita Cuisine")
                assert event.date.month == 4
                assert event.date.day == 2
                assert event.date.year == 2026
                assert event.start_time.hour == 11
                assert event.end_time.hour == 14

    @pytest.mark.asyncio
    @freeze_time("2025-12-01")
    async def test_year_rollover(
        self, parser: WaFoodTrucksParser
    ) -> None:
        """Test handling of year rollover (parsing Jan dates in Dec)."""
        json_response = {
            "mainContent": "<h3>January 15th - Future Food Truck</h3>"
        }
        
        with aioresponses() as m:
            m.get(re.compile(r".*format=json.*"), status=200, payload=json_response)

            async with aiohttp.ClientSession() as session:
                events = await parser.parse(session)
                assert len(events) == 1
                assert events[0].date.year == 2026

import re
