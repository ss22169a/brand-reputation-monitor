"""
Google Search scraper using Playwright
Uses a real browser to bypass anti-scraping
"""
import asyncio
from datetime import datetime
from typing import List
from playwright.async_api import async_playwright, Browser
from .base import BaseScraper, Review
from nlp.keywords import PROBLEM_KEYWORDS


class PlaywrightGoogleScraper(BaseScraper):
    """Scrape Google Search results using real browser with Playwright"""
    
    def __init__(self, brand_name: str):
        super().__init__(brand_name)
        self.browser: Browser = None
        self.playwright = None
    
    async def scrape(self) -> List[Review]:
        """Scrape Google search results for brand"""
        print(f"\n[Playwright Google] 啟動瀏覽器搜尋: {self.brand_name}")
        
        reviews = []
        
        try:
            # Initialize Playwright
            self.playwright = await async_playwright().start()
            
            # Use headless Chrome
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            
            # Generate search queries
            queries = self._generate_search_queries()
            
            for query in queries[:3]:  # Limit to 3 queries to save time
                try:
                    print(f"  🔍 搜尋: {query}")
                    results = await self._search_with_browser(query)
                    reviews.extend(results)
                    print(f"    ✓ 找到 {len(results)} 個結果")
                except Exception as e:
                    print(f"    ✗ 錯誤: {e}")
                    continue
            
            # Remove duplicates by URL
            seen_urls = set()
            unique_reviews = []
            for review in reviews:
                if review.url not in seen_urls:
                    seen_urls.add(review.url)
                    unique_reviews.append(review)
            
            print(f"✓ 總共 {len(unique_reviews)} 篇獨特結果\n")
            
            return unique_reviews
        
        finally:
            # Clean up
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
    
    async def scrape_by_url(self, url: str) -> List[Review]:
        """Not implemented for Playwright version"""
        return []
    
    def _generate_search_queries(self) -> List[str]:
        """Generate search queries combining brand + problem keywords"""
        queries = []
        
        # Base queries
        queries.append(f"{self.brand_name} 評論")
        queries.append(f"{self.brand_name} review")
        queries.append(f"{self.brand_name} 缺點")
        
        # Add problem keywords
        for category, keywords in PROBLEM_KEYWORDS.items():
            if category in ["quality", "price", "service"]:
                keyword = keywords[0]  # First keyword
                query = f"{self.brand_name} {keyword}"
                if query not in queries:
                    queries.append(query)
        
        return queries
    
    async def _search_with_browser(self, query: str) -> List[Review]:
        """Use Playwright to search Google and extract results"""
        reviews = []
        
        try:
            # Create new page
            page = await self.browser.new_page()
            
            # Set realistic user agent
            await page.set_extra_http_headers({
                "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            })
            
            # Navigate to Google
            search_url = f"https://www.google.com/search?q={query}"
            await page.goto(search_url, wait_until="networkidle")
            
            # Wait a bit for results to load
            await page.wait_for_timeout(2000)
            
            # Extract search results
            results = await page.evaluate("""() => {
                const results = [];
                const items = document.querySelectorAll('div[data-sokoban-container]');
                
                items.forEach(item => {
                    try {
                        const titleElem = item.querySelector('h3');
                        const linkElem = item.querySelector('a');
                        const descElem = item.querySelector('div[style*="color"]');
                        
                        if (titleElem && linkElem) {
                            results.push({
                                title: titleElem.textContent.trim(),
                                url: linkElem.href,
                                description: descElem ? descElem.textContent.trim() : ''
                            });
                        }
                    } catch (e) {}
                });
                
                return results;
            }""")
            
            # Convert to Review objects
            for result in results[:5]:  # Limit to 5 results per query
                if not result['title'] or not result['url']:
                    continue
                
                # Filter: must be relevant
                if not self._is_relevant(result['title'], result['description'], query):
                    continue
                
                review = Review(
                    source="google",
                    title=result['title'],
                    content=result['description'][:500],
                    author="Google Search",
                    rating=None,
                    url=result['url'],
                    scraped_at=datetime.now(),
                    posted_at=None,
                )
                reviews.append(review)
            
            await page.close()
        
        except Exception as e:
            print(f"    瀏覽器錯誤: {e}")
        
        return reviews
    
    def _is_relevant(self, title: str, description: str, query: str) -> bool:
        """Check if result is relevant"""
        full_text = f"{title} {description}".lower()
        
        # Must mention brand
        if self.brand_name.lower() not in full_text:
            return False
        
        # Should not be ads or unwanted results
        if any(word in full_text for word in ['廣告', 'sponsored', '購物']):
            return False
        
        return True


# Test
async def test_playwright_scraper():
    scraper = PlaywrightGoogleScraper("Apple")
    print("測試 Playwright Google 爬蟲")
    print("=" * 60)
    
    reviews = await scraper.scrape()
    
    print(f"找到 {len(reviews)} 篇結果\n")
    
    for i, review in enumerate(reviews[:5], 1):
        print(f"{i}. {review.title}")
        print(f"   {review.content[:80]}...")
        print(f"   來自: {review.url[:70]}...")
        print()


if __name__ == "__main__":
    asyncio.run(test_playwright_scraper())
