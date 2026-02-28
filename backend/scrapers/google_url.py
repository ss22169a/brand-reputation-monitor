"""
Google Search results scraper from user-provided URLs
User provides a Google search URL, we extract and analyze the results
"""
import asyncio
from datetime import datetime
from typing import List
from urllib.parse import urlparse, parse_qs
import httpx
from bs4 import BeautifulSoup
from .base import BaseScraper, Review


class GoogleUrlScraper(BaseScraper):
    """Scrape Google Search results from user-provided URL"""
    
    def __init__(self, brand_name: str, google_url: str = None):
        super().__init__(brand_name)
        self.google_url = google_url
        self.timeout = 15
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        }
    
    async def scrape(self) -> List[Review]:
        """Scrape Google search results from provided URL"""
        
        if not self.google_url:
            print(f"[Google URL] 沒有提供 URL")
            return []
        
        print(f"[Google URL] 解析 Google 搜尋頁面")
        print(f"  URL: {self.google_url[:80]}...")
        
        try:
            reviews = await self._fetch_and_parse()
            print(f"  ✓ 找到 {len(reviews)} 個搜尋結果")
            return reviews
        except Exception as e:
            print(f"  ✗ 錯誤: {e}")
            return []
    
    async def scrape_by_url(self, url: str) -> List[Review]:
        """Not used in this version"""
        return []
    
    async def _fetch_and_parse(self) -> List[Review]:
        """Fetch Google search page and extract results"""
        reviews = []
        
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                # Fetch the Google search page
                response = await client.get(self.google_url)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find search result containers
                # Google uses different selectors, try multiple
                results = []
                
                # Try multiple CSS selectors for different Google layouts
                selectors = [
                    'div[data-sokoban-container]',
                    'div.g',
                    'div[jsname="N8/gqb"]',
                    'div.Gvuyqc'
                ]
                
                for selector in selectors:
                    results = soup.select(selector)
                    if results:
                        print(f"  找到 {len(results)} 個結果 (selector: {selector})")
                        break
                
                if not results:
                    print(f"  ⚠️ 找不到結果容器")
                    return []
                
                # Extract each result
                for result in results[:10]:  # Limit to 10 results
                    try:
                        # Find title and link
                        link = result.find('a', href=True)
                        title_elem = result.find('h3')
                        
                        if not link or not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        url = link.get('href', '')
                        
                        # Clean URL (remove Google redirect parameters)
                        if url.startswith('/url?q='):
                            url = url.split('?q=')[1].split('&')[0]
                        elif not url.startswith('http'):
                            continue
                        
                        # Find description
                        description = ""
                        desc_elem = result.find('div', class_='VwiC3b')
                        if not desc_elem:
                            desc_elem = result.find('div', class_='s')
                        if not desc_elem:
                            # Try to find any span with text
                            span = result.find('span')
                            if span:
                                description = span.get_text(strip=True)
                        else:
                            description = desc_elem.get_text(strip=True)
                        
                        if not title or not url:
                            continue
                        
                        # Create review object
                        review = Review(
                            source="google",
                            title=title,
                            content=description[:500],
                            author="Google Search",
                            rating=None,
                            url=url,
                            scraped_at=datetime.now(),
                            posted_at=None,
                        )
                        reviews.append(review)
                        
                    except Exception as e:
                        continue
        
        except Exception as e:
            print(f"  無法取得頁面: {e}")
        
        return reviews


# Test
async def test_google_url_scraper():
    # Test with a real Google search URL
    url = "https://www.google.com/search?q=Apple+評論"
    scraper = GoogleUrlScraper("Apple", url)
    
    print("測試 Google URL 爬蟲")
    print("=" * 60)
    
    reviews = await scraper.scrape()
    
    print(f"\n找到 {len(reviews)} 篇結果\n")
    
    for i, review in enumerate(reviews[:5], 1):
        print(f"{i}. {review.title}")
        print(f"   {review.content[:80]}...")
        print(f"   來自: {review.url[:70]}...")
        print()


if __name__ == "__main__":
    asyncio.run(test_google_url_scraper())
