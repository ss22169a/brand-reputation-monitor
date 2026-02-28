"""
Dcard scraper for brand monitoring
Dcard is a popular Taiwanese social platform for reviews and discussions
"""
import asyncio
from datetime import datetime
from typing import List
import httpx
from .base import BaseScraper, Review


class DcardScraper(BaseScraper):
    """Scrape reviews and discussions from Dcard"""
    
    def __init__(self, brand_name: str, timeout: int = 10):
        super().__init__(brand_name)
        self.timeout = timeout
        self.base_url = "https://www.dcard.tw/api/v2"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    
    async def scrape(self) -> List[Review]:
        """
        Scrape posts mentioning the brand from Dcard
        Searches popular forums: review, shopping, bargain
        """
        forums = ["review", "shopping", "bargain"]
        reviews = []
        
        for forum in forums:
            try:
                forum_reviews = await self._scrape_forum(forum)
                reviews.extend(forum_reviews)
            except Exception as e:
                print(f"Error scraping forum '{forum}': {e}")
        
        return reviews
    
    async def scrape_by_url(self, url: str) -> List[Review]:
        """
        Scrape a specific Dcard post
        """
        try:
            # Extract post ID from URL if possible
            # Format: https://www.dcard.tw/f/{forum}/p/{post_id}
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                # Simple text extraction (Dcard is JavaScript-heavy, need Playwright for full)
                return self._parse_post_html(response.text)
        except Exception as e:
            print(f"Error scraping URL {url}: {e}")
            return []
    
    async def _scrape_forum(self, forum: str) -> List[Review]:
        """Scrape posts from a specific forum"""
        try:
            # Dcard API endpoint for posts
            url = f"{self.base_url}/forums/{forum}/posts"
            params = {
                "limit": 30,  # Get 30 most recent posts
                "sort": "new"
            }
            
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                reviews = self._parse_posts(data, forum)
                return reviews
                
        except Exception as e:
            print(f"Error accessing forum {forum}: {e}")
            return []
    
    def _parse_posts(self, data: list, forum: str) -> List[Review]:
        """Parse posts from Dcard API response"""
        reviews = []
        
        try:
            for post in data:
                # Filter posts mentioning the brand
                if not self._contains_brand(post.get("title", "") + " " + post.get("content", "")):
                    continue
                
                review = Review(
                    source="dcard",
                    title=post.get("title", ""),
                    content=post.get("content", "")[:500],  # Limit content
                    author=post.get("author", {}).get("name", "Anonymous"),
                    rating=None,  # Dcard doesn't have ratings
                    url=f"https://www.dcard.tw/f/{forum}/p/{post.get('id', '')}",
                    scraped_at=datetime.now(),
                    posted_at=self._parse_timestamp(post.get("createdAt")),
                )
                reviews.append(review)
        except Exception as e:
            print(f"Error parsing posts: {e}")
        
        return reviews
    
    def _contains_brand(self, text: str) -> bool:
        """Check if text mentions the brand"""
        text_lower = text.lower()
        brand_lower = self.brand_name.lower()
        
        # Simple substring check
        return brand_lower in text_lower
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime | None:
        """Parse ISO timestamp from Dcard"""
        try:
            if timestamp_str:
                # Dcard uses ISO format
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except:
            pass
        return None
    
    def _parse_post_html(self, html: str) -> List[Review]:
        """Parse single post HTML (simplified)"""
        # This would require BeautifulSoup or Playwright for real implementation
        # For now, return empty
        return []


# Mock test function (for development without actual API calls)
async def test_dcard_scraper():
    """Test the Dcard scraper"""
    
    # Create mock response for testing
    mock_data = [
        {
            "id": "123456",
            "title": "Apple iPhone 15 真的值得買嗎？",
            "content": "最近想買iPhone 15，但評價有好有壞。品質不錯但價格有點貴。",
            "author": {"name": "user123"},
            "createdAt": "2024-01-01T10:00:00Z"
        },
        {
            "id": "123457",
            "title": "Apple 維修體驗分享",
            "content": "到Apple授權維修店，服務態度很好，效率也高。值得推薦！",
            "author": {"name": "user456"},
            "createdAt": "2024-01-02T10:00:00Z"
        },
        {
            "id": "123458",
            "title": "買Apple產品的缺點",
            "content": "最近買MacBook，發現容易過熱，有點失望。而且維修費用超貴。",
            "author": {"name": "user789"},
            "createdAt": "2024-01-03T10:00:00Z"
        }
    ]
    
    scraper = DcardScraper(brand_name="Apple")
    
    print("Testing Dcard Scraper (Mock Data)")
    print("=" * 60)
    print(f"Brand: {scraper.brand_name}\n")
    
    # Manually parse mock data
    reviews = scraper._parse_posts(mock_data, "review")
    
    print(f"Found {len(reviews)} matching posts\n")
    
    for i, review in enumerate(reviews, 1):
        print(f"Post {i}:")
        print(f"  Title: {review.title}")
        print(f"  Content: {review.content[:100]}...")
        print(f"  Author: {review.author}")
        print(f"  URL: {review.url}")
        print(f"  Posted: {review.posted_at}")
        print()


if __name__ == "__main__":
    asyncio.run(test_dcard_scraper())
