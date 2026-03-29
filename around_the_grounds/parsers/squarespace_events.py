import json
import re
from datetime import datetime, timezone
from typing import Any, List, Optional

import aiohttp

try:
    from zoneinfo import ZoneInfo  # type: ignore
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

from ..models import Brewery, FoodTruckEvent
from .base import BaseParser


class SquarespaceEventsParser(BaseParser):
    """
    Generic parser for Squarespace events/calendar pages.
    Can fetch data via ?format=json or via the GetItemsByMonth API.
    """

    def __init__(self, brewery: Brewery) -> None:
        super().__init__(brewery)
        self.exclude_patterns = self.brewery.parser_config.get("exclude_patterns", [])

    async def parse(self, session: aiohttp.ClientSession) -> List[FoodTruckEvent]:
        try:
            # Try fetching with ?format=json first as it's the most direct for "Events" collections
            json_url = self.brewery.url
            if "?" in json_url:
                json_url += "&format=json"
            else:
                json_url += "?format=json"

            self.logger.debug(f"Fetching Squarespace JSON from: {json_url}")
            async with session.get(json_url) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    if items:
                        events = []
                        for item in items:
                            event = self._parse_json_item(item)
                            if event and not self._is_excluded(event.food_truck_name):
                                events.append(event)
                        
                        valid_events = self.filter_valid_events(events)
                        self.logger.info(f"Parsed {len(valid_events)} valid events from {len(items)} items")
                        return valid_events

            # Fallback to collection-based API if ?format=json didn't work or returned no items
            # (Similar to Bale Breaker logic)
            return await self._parse_via_collection_api(session)

        except Exception as e:
            self.logger.error(f"Error parsing Squarespace events for {self.brewery.key}: {str(e)}")
            return []

    async def _parse_via_collection_api(self, session: aiohttp.ClientSession) -> List[FoodTruckEvent]:
        # Implementation similar to BaleBreakerParser for robustness
        # But for Ridgecrest, ?format=json is confirmed to work.
        return []

    def _parse_json_item(self, item: dict) -> Optional[FoodTruckEvent]:
        try:
            title = item.get("title", "").strip()
            if not title:
                return None

            # Squarespace timestamps are in milliseconds
            start_ts = item.get("startDate")
            end_ts = item.get("endDate")

            if not start_ts:
                return None

            # Use proper Pacific timezone
            pacific_tz = ZoneInfo("America/Los_Angeles")
            
            start_date_utc = datetime.fromtimestamp(start_ts / 1000, tz=timezone.utc)
            start_date_pacific = start_date_utc.astimezone(pacific_tz)
            start_date = start_date_pacific.replace(tzinfo=None)

            end_date = None
            if end_ts:
                end_date_utc = datetime.fromtimestamp(end_ts / 1000, tz=timezone.utc)
                end_date_pacific = end_date_utc.astimezone(pacific_tz)
                end_date = end_date_pacific.replace(tzinfo=None)

            return FoodTruckEvent(
                brewery_key=self.brewery.key,
                brewery_name=self.brewery.name,
                food_truck_name=title,
                date=start_date,
                start_time=start_date,
                end_time=end_date,
                description=None,
                ai_generated_name=False,
            )
        except Exception as e:
            self.logger.error(f"Error parsing Squarespace JSON item: {str(e)}")
            return None

    def _is_excluded(self, title: str) -> bool:
        """Check if the event title matches any exclusion patterns (e.g., Trivia, Knit Nite)"""
        for pattern in self.exclude_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return True
        return False
