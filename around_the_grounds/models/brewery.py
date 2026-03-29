from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Brewery:
    key: str
    name: str
    url: str
    website_url: Optional[str] = None
    parser_config: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.parser_config is None:
            self.parser_config = {}
