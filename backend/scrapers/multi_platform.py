"""
Multi-platform scraper using keyword library
Combines all scrapers and applies intelligent search strategies
"""
import asyncio
from datetime import datetime
from typing import List
from .base import BaseScraper, Review
from .dcard import DcardScraper
from nlp.keywords import get_search_keywords_for_brand, PROBLEM_KEYWORDS, extract_problem_keywords
import httpx


class MultiPlatformScraper:
    """
    Meta-scraper that coordinates across multiple platforms
    Uses keyword library for intelligent search
    """
    
    def __init__(self, brand_name: str):
        self.brand_name = brand_name
        self.keyword_strategy = get_search_keywords_for_brand(brand_name)
        self.all_reviews = []
    
    async def scrape(self) -> List[Review]:
        """
        Scrape brand from multiple platforms
        """
        print(f"\n🎯 開始監控品牌: {self.brand_name}")
        print(f"📚 使用詞庫策略:\n")
        
        # Show strategy
        for platform, instruction in self.keyword_strategy["instructions"].items():
            print(f"  • {platform}: 用問題詞彙而非品牌名搜尋")
        
        # Scrape from Dcard (most reliable)
        print(f"\n📍 Dcard:")
        dcard_reviews = await self._scrape_dcard_smart()
        self.all_reviews.extend(dcard_reviews)
        print(f"  ✓ 找到 {len(dcard_reviews)} 篇相關貼文")
        
        # Future: Add other platforms
        # print(f"\n📍 PTT:")
        # ptt_reviews = await self._scrape_ptt_smart()
        
        # print(f"\n📍 Instagram:")
        # ig_reviews = await self._scrape_instagram_smart()
        
        print(f"\n✨ 總共收集: {len(self.all_reviews)} 篇評論")
        
        return self.all_reviews
    
    async def _scrape_dcard_smart(self) -> List[Review]:
        """
        Smart Dcard scraping:
        1. Search with brand name + problem keywords
        2. Filter by relevance
        3. Extract post-level data
        """
        reviews = []
        
        try:
            # Use Dcard scraper but with improved logic
            scraper = DcardScraper(self.brand_name)
            
            # Get posts from all forums
            forums = ["all", "recommend", "shopping", "bargain"]
            
            for forum in forums:
                try:
                    forum_reviews = await scraper._scrape_forum_smart(
                        forum, 
                        self.brand_name,
                        PROBLEM_KEYWORDS
                    )
                    reviews.extend(forum_reviews)
                except Exception as e:
                    print(f"    ✗ {forum}: {e}")
        
        except Exception as e:
            print(f"  ✗ Dcard 爬蟲錯誤: {e}")
        
        return reviews


# Test
async def test_multi_platform():
    scraper = MultiPlatformScraper("BLANK SPACE")
    reviews = await scraper.scrape()
    
    print(f"\n\n📊 結果:")
    for i, r in enumerate(reviews[:5], 1):
        print(f"{i}. {r.title}")
        print(f"   {r.content[:80]}...")
        print(f"   來自: {r.source}")
        print()


if __name__ == "__main__":
    asyncio.run(test_multi_platform())
