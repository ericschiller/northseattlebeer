import re
from datetime import datetime
from typing import List, Optional, Tuple

import aiohttp
from bs4 import BeautifulSoup

from ..models import Brewery, FoodTruckEvent
from ..utils.timezone_utils import now_in_pacific_naive
from .base import BaseParser


class WaFoodTrucksParser(BaseParser):
    """
    Parser for Washington State Food Truck Association (wafoodtrucks.org) pages.
    These are Squarespace pages where the schedule is often in a text block
    with a format like "Month Day - Truck Name".
    """

    def __init__(self, brewery: Brewery) -> None:
        super().__init__(brewery)

    async def parse(self, session: aiohttp.ClientSession) -> List[FoodTruckEvent]:
        try:
            # Fetch with ?format=json to get the structured content
            json_url = self.brewery.url
            if "?" in json_url:
                json_url += "&format=json"
            else:
                json_url += "?format=json"

            self.logger.debug(f"Fetching WA Food Trucks JSON from: {json_url}")
            async with session.get(json_url) as response:
                if response.status != 200:
                    self.logger.error(f"Failed to fetch {json_url}: {response.status}")
                    return []
                
                data = await response.json()
                html_content = data.get("mainContent", "")
                if not html_content:
                    self.logger.warning("No mainContent found in JSON response")
                    return []

                soup = BeautifulSoup(html_content, "html.parser")
                events = self._parse_html_content(soup)
                
                valid_events = self.filter_valid_events(events)
                self.logger.info(f"Parsed {len(valid_events)} valid events for {self.brewery.key}")
                return valid_events

        except Exception as e:
            self.logger.error(f"Error parsing WA Food Trucks for {self.brewery.key}: {str(e)}")
            return []

    def _parse_html_content(self, soup: BeautifulSoup) -> List[FoodTruckEvent]:
        events = []
        # The schedule is often in h3 or p tags
        elements = soup.find_all(["h3", "p"])
        
        # Regex to match "Month Day - Truck Name" or "Month Dayth - Truck Name"
        # Examples: "April 2nd - La Costenita Cuisine", "May 5th - Taco Cortes"
        date_truck_pattern = r"([A-Z][a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\s*[-–—]\s*(.*)"
        
        current_year = now_in_pacific_naive().year

        for el in elements:
            text = el.get_text(strip=True)
            if not text:
                continue
            
            match = re.search(date_truck_pattern, text)
            if match:
                month_str = match.group(1)
                day_str = match.group(2)
                truck_name = match.group(3).strip()
                
                # Cleanup truck name (sometimes there's a link or trailing info)
                # If there's a link inside, the text might already be clean enough
                # but let's make sure we don't have multiple entries in one tag
                
                event_date = self._parse_date(month_str, day_str, current_year)
                if event_date:
                    # Default time for lunch is 11am - 2pm based on page text
                    start_time = event_date.replace(hour=11, minute=0, second=0, microsecond=0)
                    end_time = event_date.replace(hour=14, minute=0, second=0, microsecond=0)
                    
                    events.append(FoodTruckEvent(
                        brewery_key=self.brewery.key,
                        brewery_name=self.brewery.name,
                        food_truck_name=truck_name,
                        date=event_date,
                        start_time=start_time,
                        end_time=end_time,
                        description="Food Truck",
                        ai_generated_name=False
                    ))
        
        return events

    def _parse_date(self, month_name: str, day: str, year: int) -> Optional[datetime]:
        try:
            # Map month names to numbers
            month_map = {
                "January": 1, "February": 2, "March": 3, "April": 4,
                "May": 5, "June": 6, "July": 7, "August": 8,
                "September": 9, "October": 10, "November": 11, "December": 12
            }
            month = month_map.get(month_name)
            if not month:
                return None
            
            dt = datetime(year, month, int(day))
            
            # Handle year rollover if we're at the end of the year and parsing Jan/Feb
            now = now_in_pacific_naive()
            if now.month >= 10 and month <= 3:
                dt = dt.replace(year=year + 1)
            elif now.month <= 3 and month >= 10:
                dt = dt.replace(year=year - 1)
                
            return dt
        except ValueError:
            return None
