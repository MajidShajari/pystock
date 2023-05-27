import locale
from typing import List
from dataclasses import dataclass, field


@dataclass
class Stock:
    current_id: str
    symbol: str = ""
    name: str = ""
    instrument_id: str = ""
    old_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.name = self.name.replace('\u200c', ' ')
        self.name = self.name.replace("  ", " ")

    def __hash__(self):
        """Hash function is used for deduplication"""
        return hash(self.symbol)

    def __lt__(self, other):
        return not locale.strcoll(other.symbol, self.symbol) < 0

    def __eq__(self, other):
        return locale.strcoll(other.symbol, self.symbol) == 0
