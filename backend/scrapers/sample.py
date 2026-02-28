"""
Sample data scraper for testing
This uses mock data to demonstrate the system without real API calls
"""
import asyncio
from datetime import datetime, timedelta
from typing import List
from .base import BaseScraper, Review


# Template for generating sample reviews dynamically
REVIEW_TEMPLATES = {
    "positive": [
        "對{brand}的購物體驗很滿意，物流迅速，商品品質不錯，賣家態度很好。",
        "{brand}的服務品質超好，客服態度親切，強烈推薦。",
        "使用{brand}已經多次，每次都很愉快，絕對信得過。",
        "{brand}的產品性能出色，物超所值，非常值得購買。",
        "在{brand}買東西體驗很好，包裝精美，送貨也快。",
    ],
    "negative": [
        "{brand}的服務太差了，商品描述和實際不符，品質令人失望。",
        "從{brand}買的東西有問題，客服態度極差，根本不想理我。",
        "{brand}的退貨流程太麻煩，售後服務非常不專業。",
        "{brand}的價格太貴，品質卻一般，根本不值這個價錢。",
        "{brand}送來的商品有瑕疵，退貨還要自己付運費，太黑心了。",
    ],
    "suggestion": [
        "{brand}產品不錯，不過希望能降低運費會更好。",
        "{brand}服務還可以，建議改進包裝和物流速度。",
        "{brand}整體不錯，但希望能有更多支付方式。",
        "用過{brand}幾次，還不錯，不過客服反應速度可以加快。",
        "{brand}的商品品質可以，建議改善退貨政策。",
    ]
}

PLATFORMS = ["dcard", "ptt", "threads", "instagram", "google_search"]


class SampleScraper(BaseScraper):
    """Scraper that generates sample reviews for testing"""
    
    def __init__(self, brand_name: str):
        super().__init__(brand_name)
        # Seed random generator with brand name for consistency
        import random
        random.seed(hash(brand_name))
    
    async def scrape(self) -> List[Review]:
        """Generate sample reviews for the brand"""
        # Simulate network delay
        await asyncio.sleep(0.5)
        
        import random
        
        reviews = []
        
        # Generate 8-12 random reviews
        num_reviews = random.randint(8, 12)
        
        for i in range(num_reviews):
            # Randomly choose sentiment type
            sentiment_type = random.choice(["positive", "negative", "positive", "suggestion"])
            templates = REVIEW_TEMPLATES[sentiment_type]
            content = random.choice(templates).format(brand=self.brand_name)
            
            # Generate title
            title_templates = {
                "positive": [
                    f"對{self.brand_name}的評價很好",
                    f"{self.brand_name}值得推薦",
                    f"在{self.brand_name}購物的經驗",
                ],
                "negative": [
                    f"{self.brand_name}讓我很失望",
                    f"{self.brand_name}的問題",
                    f"我對{self.brand_name}的不滿",
                ],
                "suggestion": [
                    f"{self.brand_name}改進建議",
                    f"{self.brand_name}可以更好",
                    f"對{self.brand_name}的看法",
                ]
            }
            title = random.choice(title_templates.get(sentiment_type, ["評論"]))
            
            # Random author
            author = f"user_{random.randint(1000, 9999)}"
            
            # Random platform
            platform = random.choice(PLATFORMS)
            
            # Generate varied timestamps
            days_ago = i + random.randint(1, 30)
            posted_at = datetime.now() - timedelta(days=days_ago)
            
            # Generate realistic URLs for each platform
            platform_urls = {
                "dcard": f"https://www.dcard.tw/f/all?keyword={self.brand_name}",
                "ptt": f"https://www.ptt.cc/bbs/Gossiping/search?q={self.brand_name}",
                "threads": f"https://www.threads.net/search?q={self.brand_name}",
                "instagram": f"https://www.instagram.com/explore/tags/{self.brand_name}/",
                "google_search": f"https://www.google.com/search?q={self.brand_name}+評論"
            }
            
            url = platform_urls.get(platform, "https://www.google.com/search?q=" + self.brand_name)
            
            review = Review(
                source=platform,
                title=title,
                content=content,
                author=author,
                rating=None,
                url=url,
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
        # Test with different brand names
        brands = ["蝦皮", "Apple", "Google"]
        
        for brand in brands:
            scraper = SampleScraper(brand)
            reviews = await scraper.scrape()
            
            print(f"\n{brand} - Found {len(reviews)} reviews:")
            for i, r in enumerate(reviews[:3], 1):
                print(f"  {i}. {r.title} ({r.source})")
    
    asyncio.run(test())
