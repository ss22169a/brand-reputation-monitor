"""
Google Search scraper for brand monitoring
Scrapes search results using BeautifulSoup
"""
import asyncio
from datetime import datetime
from typing import List
import httpx
from bs4 import BeautifulSoup
from .base import BaseScraper, Review
from nlp.keywords import PROBLEM_KEYWORDS


class GoogleSearchScraper(BaseScraper):
    """Scrape Google Search results for brand reviews"""
    
    def __init__(self, brand_name: str, timeout: int = 15):
        super().__init__(brand_name)
        self.timeout = timeout
        self.base_url = "https://www.google.com/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
    
    async def scrape(self) -> List[Review]:
        """Scrape Google search results for brand"""
        print(f"[Google] 搜尋品牌: {self.brand_name}")
        
        reviews = []
        
        # Generate search queries combining brand + problem keywords
        queries = self._generate_search_queries()
        
        for query in queries:
            try:
                results = await self._search(query)
                reviews.extend(results)
            except Exception as e:
                print(f"  ✗ 查詢失敗: {query[:30]}... {e}")
        
        # Remove duplicates by URL
        seen_urls = set()
        unique_reviews = []
        for review in reviews:
            if review.url not in seen_urls:
                seen_urls.add(review.url)
                unique_reviews.append(review)
        
        return unique_reviews
    
    async def scrape_by_url(self, url: str) -> List[Review]:
        """Scrape a specific URL"""
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Extract title and meta description from HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.find('title')
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                
                review = Review(
                    source="google",
                    title=title.text if title else "未知標題",
                    content=meta_desc.get('content', '')[:500] if meta_desc else "無描述",
                    author="Google",
                    rating=None,
                    url=url,
                    scraped_at=datetime.now(),
                    posted_at=None,
                )
                return [review]
        except Exception as e:
            print(f"無法取得 URL: {e}")
            return []
    
    def _generate_search_queries(self) -> List[str]:
        """Generate search queries combining brand + problem keywords"""
        queries = []
        
        # Base query
        queries.append(f"{self.brand_name} 評論")
        queries.append(f"{self.brand_name} review")
        
        # Combine with problem keywords
        for category, keywords in PROBLEM_KEYWORDS.items():
            # Pick top keywords for this category
            top_keywords = keywords[:2]  # First 2 keywords
            for keyword in top_keywords:
                query = f"{self.brand_name} {keyword}"
                if query not in queries:
                    queries.append(query)
        
        return queries[:5]  # Limit to 5 queries to avoid too many requests
    
    async def _search(self, query: str) -> List[Review]:
        """Search Google and extract results"""
        reviews = []
        
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                params = {
                    "q": query,
                    "num": 10,  # Number of results
                }
                
                url = f"{self.base_url}"
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find search result containers
                results = soup.find_all('div', class_='g')
                
                print(f"  📍 '{query}': 找到 {len(results)} 個結果")
                
                for result in results:
                    try:
                        # Extract title
                        title_elem = result.find('h3')
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)
                        
                        # Extract URL
                        link_elem = result.find('a')
                        if not link_elem or not link_elem.get('href'):
                            continue
                        url = link_elem.get('href')
                        
                        # Clean up URL (remove Google redirect)
                        if url.startswith('/url?q='):
                            url = url.split('?q=')[1].split('&')[0]
                        
                        # Extract meta description
                        desc_elem = result.find('div', class_='s')
                        description = ""
                        if desc_elem:
                            description = desc_elem.get_text(strip=True)[:500]
                        
                        # Only include if description mentions brand or problem keywords
                        if not self._is_relevant(title, description, query):
                            continue
                        
                        review = Review(
                            source="google",
                            title=title,
                            content=description,
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
            print(f"  ✗ 搜尋錯誤: {e}")
        
        return reviews
    
    def _is_relevant(self, title: str, description: str, query: str) -> bool:
        """Check if result is relevant"""
        full_text = f"{title} {description}".lower()
        
        # Must mention brand
        if self.brand_name.lower() not in full_text:
            return False
        
        # Should contain some keyword from query
        query_words = query.lower().split()
        return any(word in full_text for word in query_words if len(word) > 2)


# Test
async def test_google_scraper():
    scraper = GoogleSearchScraper("Apple")
    print("測試 Google Search 爬蟲")
    print("=" * 60)
    
    try:
        reviews = await scraper.scrape()
        
        print(f"\n找到 {len(reviews)} 篇結果\n")
        
        for i, review in enumerate(reviews[:5], 1):
            print(f"{i}. {review.title}")
            print(f"   {review.content[:80]}...")
            print(f"   URL: {review.url[:60]}...")
            print()
    except Exception as e:
        print(f"錯誤: {e}")


if __name__ == "__main__":
    asyncio.run(test_google_scraper())
