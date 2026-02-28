"""
Google Search scraper for brand monitoring
Searches for brand mentions and reviews on Google
"""
import asyncio
from datetime import datetime
from typing import List
from urllib.parse import urlencode
import httpx
from bs4 import BeautifulSoup
from .base import BaseScraper, Review


class GoogleSearchScraper(BaseScraper):
    """Scrape reviews and mentions from Google Search"""
    
    def __init__(self, brand_name: str, timeout: int = 10):
        super().__init__(brand_name)
        self.timeout = timeout
        self.base_url = "https://www.google.com/search"
        # User-Agent to avoid blocks
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    
    async def scrape(self) -> List[Review]:
        """
        Scrape reviews for the brand from Google Search
        Searches for: "{brand} 評論", "{brand} review", "{brand} 缺點"
        """
        queries = [
            f"{self.brand_name} 評論",
            f"{self.brand_name} review",
            f"{self.brand_name} 缺點",
            f"{self.brand_name} 問題",
        ]
        
        reviews = []
        for query in queries:
            try:
                query_reviews = await self._search_and_parse(query)
                reviews.extend(query_reviews)
            except Exception as e:
                print(f"Error scraping query '{query}': {e}")
        
        return reviews
    
    async def scrape_by_url(self, url: str) -> List[Review]:
        """
        Scrape reviews from a specific URL
        For Google Search, this would be a search results URL
        """
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return self._parse_search_results(response.text)
        except Exception as e:
            print(f"Error scraping URL {url}: {e}")
            return []
    
    async def _search_and_parse(self, query: str) -> List[Review]:
        """Search Google and parse results"""
        try:
            params = {
                "q": query,
                "num": 10,  # Number of results
            }
            
            url = f"{self.base_url}?{urlencode(params)}"
            
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return self._parse_search_results(response.text)
        except Exception as e:
            print(f"Error searching Google for '{query}': {e}")
            return []
    
    def _parse_search_results(self, html: str) -> List[Review]:
        """
        Parse Google Search HTML results
        Note: This is a simplified parser. Real implementation may need
        more robust parsing due to Google's dynamic content.
        """
        reviews = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find search result containers
        result_containers = soup.find_all('div', class_='g')
        
        for container in result_containers:
            try:
                # Extract title
                title_elem = container.find('h3')
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                
                # Extract URL
                link_elem = container.find('a')
                if not link_elem or not link_elem.get('href'):
                    continue
                url = link_elem.get('href')
                
                # Extract snippet (content)
                snippet_elem = container.find('div', class_='VwiC3b')
                content = ""
                if snippet_elem:
                    content = snippet_elem.get_text(strip=True)
                
                # Create review object
                review = Review(
                    source="google_search",
                    title=title,
                    content=content,
                    author="Google Search",
                    rating=None,
                    url=url,
                    scraped_at=datetime.now(),
                    posted_at=None,
                )
                
                reviews.append(review)
            except Exception as e:
                print(f"Error parsing result: {e}")
                continue
        
        return reviews


# Test function
async def test_google_scraper():
    """Test the Google Search scraper"""
    scraper = GoogleSearchScraper(brand_name="Apple")
    
    print("Testing Google Search Scraper...")
    print(f"Brand: {scraper.brand_name}")
    print("-" * 50)
    
    try:
        reviews = await scraper.scrape()
        
        print(f"\nFound {len(reviews)} results\n")
        
        for i, review in enumerate(reviews[:5], 1):
            print(f"Result {i}:")
            print(f"  Source: {review.source}")
            print(f"  Title: {review.title}")
            print(f"  Content: {review.content[:100]}...")
            print(f"  URL: {review.url}")
            print()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_google_scraper())
