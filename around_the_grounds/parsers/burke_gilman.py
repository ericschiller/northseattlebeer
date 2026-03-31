from datetime import datetime, timedelta
from typing import List, Optional

import aiohttp

from ..models import Brewery, FoodTruckEvent
from ..utils.timezone_utils import now_in_pacific_naive
from .base import BaseParser


class BurkeGilmanParser(BaseParser):
    """
    Static parser for Burke-Gilman Brewing Company.
    Uses a static schedule for recurring events and their permanent food truck.
    """

    async def parse(self, session: aiohttp.ClientSession) -> List[FoodTruckEvent]:
        events: List[FoodTruckEvent] = []
        now = now_in_pacific_naive()
        
        # Generate events for the next 14 days
        for i in range(14):
            current_date = now + timedelta(days=i)
            weekday = current_date.weekday() # 0 is Monday, 1 is Tuesday, etc.
            
            # Tuesday: King Trivia
            if weekday == 1:
                events.append(
                    FoodTruckEvent(
                        brewery_key=self.brewery.key,
                        brewery_name=self.brewery.name,
                        food_truck_name="King Trivia",
                        date=current_date.replace(hour=0, minute=0, second=0, microsecond=0),
                        start_time=current_date.replace(hour=19, minute=0, second=0, microsecond=0),
                        end_time=current_date.replace(hour=21, minute=0, second=0, microsecond=0),
                        description="Trivia",
                        category="trivia"
                    )
                )
            
            # Monday (Monthly): Smarty Pints (3rd Monday)
            # Simplified: if it's Monday and the day is between 15-21, it's the 3rd Monday
            if weekday == 0 and 15 <= current_date.day <= 21:
                events.append(
                    FoodTruckEvent(
                        brewery_key=self.brewery.key,
                        brewery_name=self.brewery.name,
                        food_truck_name="Smarty Pints",
                        date=current_date.replace(hour=0, minute=0, second=0, microsecond=0),
                        start_time=current_date.replace(hour=18, minute=30, second=0, microsecond=0),
                        end_time=current_date.replace(hour=20, minute=0, second=0, microsecond=0),
                        description="Guest speakers and beer",
                        category="community"
                    )
                )
                
        return events
