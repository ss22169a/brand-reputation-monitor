"""
Sample data scraper for testing
This uses mock data to demonstrate the system without real API calls
"""
import asyncio
from datetime import datetime, timedelta
from typing import List
from .base import BaseScraper, Review


# Sample review data for testing
SAMPLE_REVIEWS = {
    "蝦皮": [
        {
            "title": "蝦皮購物體驗不錯",
            "content": "在蝦皮買了幾次東西，物流快速，商品品質不錯。賣家態度也很好，推薦購買。",
            "author": "user_123",
            "source": "dcard"
        },
        {
            "title": "蝦皮運費有點貴",
            "content": "商品價格還可以，但運費偏高。希望能提供更便宜的物流選項。",
            "author": "user_456",
            "source": "ptt"
        },
        {
            "title": "收到瑕疵品，退貨很麻煩",
            "content": "買的手機殼有瑕疵，要求退貨，但蝦皮的退貨流程太複雜了，客服態度也不太好。",
            "author": "user_789",
            "source": "dcard"
        },
        {
            "title": "蝦皮超級黑心",
            "content": "被騙了！商品和描述不符，品質很差，客服根本不理我。再也不買蝦皮。",
            "author": "user_000",
            "source": "threads"
        },
        {
            "title": "蝦皮定期折扣很划算",
            "content": "最近買了家電，蝦皮的折扣力度不錯，省了不少錢。推薦大家關注蝦皮的促銷活動。",
            "author": "user_111",
            "source": "instagram"
        },
    ],
    "Momo": [
        {
            "title": "Momo 購物滿意度高",
            "content": "Momo 的服務品質很不錯，物流快，售後也很好。會繼續購買。",
            "author": "buyer_001",
            "source": "dcard"
        },
        {
            "title": "Momo 有時缺貨",
            "content": "想買的商品經常缺貨，網站要更新商品狀態。",
            "author": "buyer_002",
            "source": "ptt"
        },
    ],
    "Apple": [
        {
            "title": "iPhone 15 真的不值 25000 元",
            "content": "價格太貴，功能升級不明顯，不推薦買。應該等降價。",
            "author": "tech_fan_1",
            "source": "dcard"
        },
        {
            "title": "Apple 服務體驗很棒",
            "content": "去 Apple Store 維修 MacBook，服務態度很好，問題解決迅速，值得信賴。",
            "author": "apple_fan",
            "source": "threads"
        },
    ],
}


class SampleScraper(BaseScraper):
    """Scraper that returns sample data for testing"""
    
    def __init__(self, brand_name: str):
        super().__init__(brand_name)
    
    async def scrape(self) -> List[Review]:
        """Return sample reviews for the brand"""
        # Simulate network delay
        await asyncio.sleep(0.5)
        
        reviews = []
        sample_data = SAMPLE_REVIEWS.get(self.brand_name, [])
        
        for i, data in enumerate(sample_data):
            # Generate varied timestamps
            days_ago = i * 2
            posted_at = datetime.now() - timedelta(days=days_ago)
            
            review = Review(
                source=data["source"],
                title=data["title"],
                content=data["content"],
                author=data["author"],
                rating=None,
                url=f"https://sample.com/review/{i}",
                scraped_at=datetime.now(),
                posted_at=posted_at,
            )
            reviews.append(review)
        
        return reviews
    
    async def scrape_by_url(self, url: str) -> List[Review]:
        """Sample URL scraping"""
        await asyncio.sleep(0.2)
        return await self.scrape()


if __name__ == "__main__":
    async def test():
        scraper = SampleScraper("蝦皮")
        reviews = await scraper.scrape()
        
        print(f"Found {len(reviews)} reviews for {scraper.brand_name}:")
        for i, r in enumerate(reviews, 1):
            print(f"{i}. {r.title}")
    
    asyncio.run(test())
