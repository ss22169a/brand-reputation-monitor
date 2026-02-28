"""
Base scraper class - all scrapers inherit from this
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Review:
    """Review data model"""
    source: str  # 'google', 'dcard', 'ptt', 'threads', 'instagram'
    title: str
    content: str
    author: str
    rating: float | None
    url: str
    scraped_at: datetime
    posted_at: datetime | None = None


class BaseScraper(ABC):
    """Base class for all scrapers"""
    
    def __init__(self, brand_name: str):
        self.brand_name = brand_name
    
    @abstractmethod
    async def scrape(self) -> List[Review]:
        """Scrape reviews for the brand"""
        pass
    
    @abstractmethod
    async def scrape_by_url(self, url: str) -> List[Review]:
        """Scrape reviews from specific URL"""
        pass
