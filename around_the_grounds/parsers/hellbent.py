import re
from datetime import datetime, timedelta
from typing import List, Optional

import aiohttp
from bs4 import BeautifulSoup

from ..models import Brewery, FoodTruckEvent
from .base import BaseParser


class HellbentParser(BaseParser):
    """
    Parser for Hellbent Brewing Company which uses the Simple Calendar (SimCal) WordPress plugin.
    It parses the grid view of the calendar.
    """

    def __init__(self, brewery: Brewery) -> None:
        super().__init__(brewery)

    async def parse(self, session: aiohttp.ClientSession) -> List[FoodTruckEvent]:
        try:
            soup = await self.fetch_page(session, self.brewery.url)
            if not soup:
                return []

            # Find the calendar container to get the start date
            calendar_div = soup.find("div", class_="simcal-calendar")
            if not calendar_div:
                self.logger.warning("SimCal calendar container not found")
                return []

            # data-calendar-start is a Unix timestamp in seconds
            start_ts_str = calendar_div.get("data-calendar-start")
            if not start_ts_str:
                self.logger.warning("data-calendar-start attribute not found")
                return []

            calendar_start_dt = datetime.fromtimestamp(int(start_ts_str))
            
            # Simple Calendar grid view has <td> elements for each day
            # We need to find the days and their events
            events = []
            
            # Find all day cells
            day_cells = soup.find_all("td", class_=lambda c: c and "simcal-day" in c.split())
            
            for cell in day_cells:
                # Skip "void" days (padding for start/end of month)
                if "simcal-day-void" in cell.get("class", []):
                    continue
                
                # Determine the date for this cell
                # Classes are like simcal-day-1, simcal-day-2, etc.
                day_match = re.search(r"simcal-day-(\d+)", " ".join(cell.get("class", [])))
                if not day_match:
                    continue
                
                day_num = int(day_match.group(1))
                # The simcal-day-N class refers to the day of the month
                event_date = calendar_start_dt.replace(day=day_num)
                
                # Check for events in this cell
                event_items = cell.find_all("li", class_="simcal-event")
                for item in event_items:
                    # Get truck name
                    title_el = item.find(class_="simcal-event-title")
                    if not title_el:
                        continue
                        
                    truck_name = title_el.get_text(strip=True)
                    if truck_name.lower() in ["tbd", "closed"]:
                        continue
                    
                    # Extract time if available
                    start_dt, end_dt = self._parse_event_times(item, event_date)
                    
                    events.append(FoodTruckEvent(
                        brewery_key=self.brewery.key,
                        brewery_name=self.brewery.name,
                        food_truck_name=truck_name,
                        date=event_date,
                        start_time=start_dt,
                        end_time=end_dt,
                        description=None,
                    ))

            valid_events = self.filter_valid_events(events)
            self.logger.info(f"Parsed {len(valid_events)} valid events for {self.brewery.key}")
            return valid_events

        except Exception as e:
            self.logger.error(f"Error parsing Hellbent for {self.brewery.key}: {str(e)}")
            return []

    def _parse_event_times(self, item_el: BeautifulSoup, event_date: datetime) -> tuple[Optional[datetime], Optional[datetime]]:
        """Extract start and end times from the event element if present."""
        try:
            # Look for time elements
            start_time_el = item_el.find("time", class_="simcal-event-start")
            end_time_el = item_el.find("time", class_="simcal-event-end")
            
            start_dt = None
            end_dt = None
            
            if start_time_el:
                # Often there's a data-timezone-format or it's just text
                time_text = start_time_el.get_text(strip=True)
                start_dt = self._apply_time_to_date(event_date, time_text)
            
            if end_time_el:
                time_text = end_time_el.get_text(strip=True)
                end_dt = self._apply_time_to_date(event_date, time_text)
            
            # Fallback to default hours (5pm-9pm) if not found, as per web_fetch observation
            if not start_dt:
                start_dt = event_date.replace(hour=17, minute=0)
            if not end_dt:
                end_dt = event_date.replace(hour=21, minute=0)
                
            return start_dt, end_dt
        except Exception:
            # Fallback to default hours on error
            return event_date.replace(hour=17, minute=0), event_date.replace(hour=21, minute=0)

    def _apply_time_to_date(self, base_date: datetime, time_str: str) -> Optional[datetime]:
        """Convert '5:00 pm' to a datetime using base_date's day."""
        try:
            # Handle common formats like '5:00 pm', '5 pm', '17:00'
            time_str = time_str.lower().strip()
            match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", time_str)
            if not match:
                return None
                
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            ampm = match.group(3)
            
            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
                
            return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except Exception:
            return None
