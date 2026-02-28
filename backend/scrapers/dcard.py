"""
Dcard scraper for brand monitoring
Dcard is a popular Taiwanese social platform for reviews and discussions
Uses official Dcard API v2 + keyword library for better search
"""
import asyncio
from datetime import datetime
from typing import List
import httpx
from .base import BaseScraper, Review
from nlp.keywords import PROBLEM_KEYWORDS, get_search_keywords_for_brand


class DcardScraper(BaseScraper):
    """Scrape reviews and discussions from Dcard using official API"""
    
    def __init__(self, brand_name: str, timeout: int = 15):
        super().__init__(brand_name)
        self.timeout = timeout
        self.base_url = "https://www.dcard.tw/api/v2"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    async def scrape(self) -> List[Review]:
        """
        Scrape posts mentioning the brand from Dcard
        Searches across all forums
        """
        print(f"[Dcard] 搜尋品牌: {self.brand_name}")
        
        reviews = []
        
        try:
            # Search using Dcard search API
            reviews = await self._search_posts()
        except Exception as e:
            print(f"[Dcard] 搜尋失敗: {e}")
        
        return reviews
    
    async def scrape_by_url(self, url: str) -> List[Review]:
        """
        Scrape a specific Dcard post by URL
        Format: https://www.dcard.tw/f/{forum}/p/{post_id}
        """
        try:
            # Extract post ID from URL
            # Example: https://www.dcard.tw/f/all/p/123456789
            parts = url.split('/p/')
            if len(parts) != 2:
                return []
            
            post_id = parts[1].split('?')[0].split('#')[0]
            
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                api_url = f"{self.base_url}/posts/{post_id}"
                response = await client.get(api_url)
                response.raise_for_status()
                
                post = response.json()
                review = self._post_to_review(post)
                return [review] if review else []
        except Exception as e:
            print(f"[Dcard] 無法取得單一貼文: {e}")
            return []
    
    async def _search_posts(self) -> List[Review]:
        """搜尋 Dcard 貼文 (基本版本)"""
        reviews = []
        
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                forums = ["all", "recommend", "shopping"]
                
                for forum in forums:
                    try:
                        url = f"{self.base_url}/forums/{forum}/posts"
                        params = {
                            "limit": 30,
                            "sort": "new"
                        }
                        
                        response = await client.get(url, params=params, timeout=10)
                        
                        if response.status_code == 200:
                            posts = response.json()
                            
                            if isinstance(posts, list):
                                for post in posts:
                                    title = post.get("title", "")
                                    content = post.get("content", "")
                                    
                                    if self._contains_brand(title + " " + content):
                                        review = self._post_to_review(post)
                                        if review:
                                            reviews.append(review)
                        
                        print(f"  ✓ {forum}: 找到相關貼文")
                    
                    except Exception as e:
                        continue
        
        except Exception as e:
            print(f"[Dcard] 搜尋錯誤: {e}")
        
        return reviews
    
    async def _scrape_forum_smart(self, forum: str, brand_name: str, problem_keywords: dict) -> List[Review]:
        """
        Smart forum scraping using keyword strategy
        搜尋: 品牌名 + 問題詞彙的組合
        """
        reviews = []
        
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                url = f"{self.base_url}/forums/{forum}/posts"
                
                # Get recent posts
                params = {"limit": 50, "sort": "new"}
                response = await client.get(url, params=params, timeout=10)
                
                if response.status_code != 200:
                    return reviews
                
                posts = response.json()
                
                if not isinstance(posts, list):
                    return reviews
                
                # Filter posts by brand + problem keywords
                for post in posts:
                    title = post.get("title", "")
                    content = post.get("content", "")
                    full_text = f"{title} {content}".lower()
                    
                    # Check if post mentions brand
                    if not self._contains_brand_loose(full_text, brand_name):
                        continue
                    
                    # Check if post contains problem keywords
                    has_problem_keyword = False
                    for category, keywords in problem_keywords.items():
                        if any(kw in full_text for kw in keywords):
                            has_problem_keyword = True
                            break
                    
                    # If not a problem post, might still be relevant
                    # But prioritize problem posts
                    if not has_problem_keyword:
                        # Only include if mentions brand + some evaluation
                        if not any(word in full_text for word in ["好", "爛", "差", "不錯", "推薦", "踩雷"]):
                            continue
                    
                    # Convert to review
                    review = self._post_to_review(post)
                    if review:
                        reviews.append(review)
        
        except Exception as e:
            pass
        
        return reviews
    
    def _contains_brand_loose(self, text: str, brand_name: str) -> bool:
        """Loose brand matching (handles various formats)"""
        brand_lower = brand_name.lower()
        text_lower = text.lower()
        
        # Direct match
        if brand_lower in text_lower:
            return True
        
        # Remove spaces and try again
        brand_no_space = brand_lower.replace(" ", "")
        text_no_space = text_lower.replace(" ", "")
        
        if brand_no_space in text_no_space:
            return True
        
        return False
    
    def _post_to_review(self, post: dict) -> Review | None:
        """Convert Dcard post to Review object"""
        try:
            post_id = post.get("id")
            forum = post.get("school", {}).get("alias", "all") if isinstance(post.get("school"), dict) else "all"
            
            review = Review(
                source="dcard",
                title=post.get("title", "未知標題"),
                content=post.get("content", "")[:500],
                author=post.get("author", {}).get("name", "匿名") if isinstance(post.get("author"), dict) else "匿名",
                rating=None,
                url=f"https://www.dcard.tw/f/{forum}/p/{post_id}",
                scraped_at=datetime.now(),
                posted_at=self._parse_timestamp(post.get("createdAt")),
            )
            return review
        except Exception as e:
            print(f"  [Error parsing post]: {e}")
            return None
    
    def _contains_brand(self, text: str) -> bool:
        """Check if text mentions the brand"""
        if not text:
            return False
        
        text_lower = text.lower()
        brand_lower = self.brand_name.lower()
        
        # Check for exact brand name or common variations
        keywords = [brand_lower]
        
        # Add common Chinese/English variations
        if brand_lower in ["蝦皮", "shopee"]:
            keywords.extend(["蝦皮", "shopee"])
        elif brand_lower in ["momo", "momoshop"]:
            keywords.extend(["momo", "momoshop", "momo購物"])
        
        return any(keyword in text_lower for keyword in keywords)
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime | None:
        """Parse ISO timestamp from Dcard"""
        try:
            if timestamp_str:
                if isinstance(timestamp_str, str):
                    # Handle ISO format with Z
                    timestamp_str = timestamp_str.replace("Z", "+00:00")
                    return datetime.fromisoformat(timestamp_str)
        except Exception as e:
            pass
        return None


# Test function
async def test_dcard_scraper():
    """Test the Dcard scraper with real data"""
    scraper = DcardScraper(brand_name="蝦皮")
    
    print("Testing Dcard Scraper (Real Data)")
    print("=" * 60)
    
    try:
        reviews = await scraper.scrape()
        
        print(f"\n找到 {len(reviews)} 篇相關貼文\n")
        
        for i, review in enumerate(reviews[:5], 1):
            print(f"{i}. {review.title}")
            print(f"   作者: {review.author}")
            print(f"   來源: {review.url}")
            print(f"   內容: {review.content[:80]}...")
            print()
    except Exception as e:
        print(f"錯誤: {e}")


if __name__ == "__main__":
    asyncio.run(test_dcard_scraper())
