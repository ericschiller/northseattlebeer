"""Tests for Hellbent Brewing Company parser."""

import re
from datetime import datetime
from typing import Any, Dict

import aiohttp
import pytest
from bs4 import BeautifulSoup

from around_the_grounds.models import Brewery
from around_the_grounds.parsers.hellbent import HellbentParser


class TestHellbentParser:
    """Test the HellbentParser class."""

    @pytest.fixture
    def brewery(self) -> Brewery:
        """Create a test brewery for Hellbent."""
        return Brewery(
            key="hellbent",
            name="Hellbent Brewing Company",
            url="https://hellbentbrewingcompany.com/food-trucks/",
            parser_config={
                "note": "WordPress site with Simple Calendar (SimCal) plugin",
                "api_type": "simcal"
            },
        )

    @pytest.fixture
    def parser(self, brewery: Brewery) -> HellbentParser:
        """Create a parser instance."""
        return HellbentParser(brewery)

    @pytest.fixture
    def sample_html(self) -> str:
        """Sample HTML with SimCal calendar."""
        # March 2026 starts on a Sunday (weekday-0)
        # 1772438400 is March 1, 2026 00:00:00 UTC
        # Let's use 1772419200 which is more like midnight Pacific
        return """
        <div class="simcal-calendar" data-calendar-start="1772419200">
            <table>
                <tr>
                    <td class="simcal-day-1 simcal-weekday-0 simcal-day">
                        <span class="simcal-day-number">1</span>
                        <ul class="simcal-events">
                            <li class="simcal-event">
                                <span class="simcal-event-title">Burger Dom</span>
                                <time class="simcal-event-start">5:00 pm</time>
                                <time class="simcal-event-end">9:00 pm</time>
                            </li>
                        </ul>
                    </td>
                    <td class="simcal-day-2 simcal-weekday-1 simcal-day">
                        <span class="simcal-day-number">2</span>
                        <ul class="simcal-events">
                            <li class="simcal-event">
                                <span class="simcal-event-title">TBD</span>
                            </li>
                        </ul>
                    </td>
                    <td class="simcal-day-3 simcal-weekday-2 simcal-day">
                        <span class="simcal-day-number">3</span>
                        <ul class="simcal-events">
                            <li class="simcal-event">
                                <span class="simcal-event-title">Tacos and Beers</span>
                            </li>
                        </ul>
                    </td>
                </tr>
            </table>
        </div>
        """

    @pytest.mark.asyncio
    async def test_parse_hellbent_html(
        self, parser: HellbentParser, sample_html: str, monkeypatch: Any
    ) -> None:
        """Test parsing Hellbent HTML content successfully."""
        
        async def mock_fetch_page(*args, **kwargs):
            return BeautifulSoup(sample_html, "html.parser")
            
        monkeypatch.setattr(parser, "fetch_page", mock_fetch_page)

        async with aiohttp.ClientSession() as session:
            events = await parser.parse(session)

            # Should have 2 events (Burger Dom and Tacos and Beers). TBD is excluded.
            assert len(events) == 2
            
            truck_names = [e.food_truck_name for e in events]
            assert "Burger Dom" in truck_names
            assert "Tacos and Beers" in truck_names
            assert "TBD" not in truck_names

            # Check specific event details
            burger_dom = next(e for e in events if e.food_truck_name == "Burger Dom")
            assert burger_dom.date.day == 1
            assert burger_dom.date.month == 3
            assert burger_dom.start_time.hour == 17
            assert burger_dom.end_time.hour == 21

            tacos = next(e for e in events if e.food_truck_name == "Tacos and Beers")
            assert tacos.date.day == 3
            # Should fallback to default 5pm-9pm
            assert tacos.start_time.hour == 17
            assert tacos.end_time.hour == 21

    @pytest.mark.asyncio
    async def test_parse_missing_calendar(self, parser: HellbentParser, monkeypatch: Any) -> None:
        """Test parsing when calendar is missing."""
        async def mock_fetch_page(*args, **kwargs):
            return BeautifulSoup("<div>No calendar here</div>", "html.parser")
            
        monkeypatch.setattr(parser, "fetch_page", mock_fetch_page)

        async with aiohttp.ClientSession() as session:
            events = await parser.parse(session)
            assert len(events) == 0
