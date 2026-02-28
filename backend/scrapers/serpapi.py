"""
SerpAPI Google Search scraper
Uses official SerpAPI to get real Google search results
"""
import asyncio
from datetime import datetime
from typing import List
import httpx
from .base import BaseScraper, Review


class SerpAPIScraper(BaseScraper):
    """Scrape Google Search results using SerpAPI"""
    
    def __init__(self, brand_name: str, api_key: str):
        super().__init__(brand_name)
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"
        self.timeout = 30
    
    async def scrape(self) -> List[Review]:
        """Scrape Google search results for brand"""
        print(f"\n[SerpAPI] 搜尋品牌: {self.brand_name}")
        
        reviews = []
        
        # Generate search queries - more comprehensive
        queries = [
            f"{self.brand_name} 評論",
            f"{self.brand_name} 缺點",
            f"{self.brand_name} 品質",
            f"{self.brand_name} 不好",
            f"{self.brand_name} review",
        ]
        
        for query in queries:  # Search all queries
            try:
                print(f"  🔍 查詢: {query}")
                results = await self._search(query)
                reviews.extend(results)
                print(f"    ✓ 找到 {len(results)} 個結果")
            except Exception as e:
                print(f"    ✗ 錯誤: {e}")
        
        # Remove duplicates by URL
        seen_urls = set()
        unique_reviews = []
        for review in reviews:
            if review.url not in seen_urls:
                seen_urls.add(review.url)
                unique_reviews.append(review)
        
        print(f"✓ 總共 {len(unique_reviews)} 個獨特結果\n")
        return unique_reviews
    
    async def scrape_by_url(self, url: str) -> List[Review]:
        """Not used"""
        return []
    
    async def _search(self, query: str) -> List[Review]:
        """Search Google via SerpAPI"""
        reviews = []
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "q": query,
                    "engine": "google",
                    "api_key": self.api_key,
                    "num": 20,  # Get 20 results instead of 10
                    "hl": "zh-TW",  # Traditional Chinese
                }
                
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Debug: print raw response
                print(f"      API 返回 {len(data.get('organic_results', []))} 個結果")
                
                # Extract organic results
                organic_results = data.get("organic_results", [])
                
                # Debug: print first result to see structure
                if organic_results:
                    print(f"      第一筆結果: {organic_results[0]}")
                
                for result in organic_results:
                    try:
                        title = result.get("title", "")
                        url = result.get("link", "")
                        snippet = result.get("snippet", "")
                        
                        # Skip if no title or no URL
                        if not title:
                            continue
                        
                        # If URL is missing but we have content, still include it
                        if not url:
                            url = ""
                        
                        review = Review(
                            source="google",
                            title=title,
                            content=snippet[:500] if snippet else "(無摘要)",
                            author="Google Search",
                            rating=None,
                            url=url,
                            scraped_at=datetime.now(),
                            posted_at=None,
                        )
                        reviews.append(review)
                        
                    except Exception as e:
                        print(f"      解析錯誤: {e}")
                        continue
        
        except Exception as e:
            print(f"      SerpAPI 錯誤: {e}")
        
        return reviews


# Test
async def test_serpapi():
    api_key = "YOUR_API_KEY"  # Replace with actual key
    scraper = SerpAPIScraper("Apple", api_key)
    
    print("測試 SerpAPI 爬蟲")
    print("=" * 60)
    
    reviews = await scraper.scrape()
    
    print(f"找到 {len(reviews)} 篇結果\n")
    
    for i, review in enumerate(reviews[:5], 1):
        print(f"{i}. {review.title}")
        print(f"   {review.content[:80]}...")
        print(f"   URL: {review.url[:70]}...")
        print()


if __name__ == "__main__":
    asyncio.run(test_serpapi())
