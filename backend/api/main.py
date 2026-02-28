"""
Main FastAPI application for Brand Reputation Monitor
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from nlp.sentiment import SentimentAnalyzer, SentimentResult
from nlp.classifier import ProblemClassifier
from scrapers.base import Review
from scrapers.serpapi import SerpAPIScraper
try:
    from routes.keywords import router as keywords_router
except ImportError:
    from .routes.keywords import router as keywords_router
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = FastAPI(
    title="Brand Reputation Monitor API",
    description="AI-powered reputation monitoring system",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(keywords_router)

# Initialize analyzers once at startup
sentiment_analyzer = None
problem_classifier = None

@app.on_event("startup")
async def startup_event():
    """Initialize NLP models on startup"""
    global sentiment_analyzer, problem_classifier
    print("初始化 NLP 模型...")
    sentiment_analyzer = SentimentAnalyzer()
    problem_classifier = ProblemClassifier()
    print("✓ 模型初始化完成")


# Pydantic models
class MonitoringRequest(BaseModel):
    """Request to monitor a brand"""
    brand_name: str


class ReviewAnalysis(BaseModel):
    """Analyzed review with sentiment and classification"""
    title: str
    content: str
    source: str
    url: str
    sentiment: str
    sentiment_score: float
    sentiment_confidence: float
    category: str
    priority: int
    keywords: List[str]


class MonitoringResponse(BaseModel):
    """Response from monitoring request"""
    brand_name: str
    total_reviews: int
    reviews: List[ReviewAnalysis]
    sentiment_distribution: dict
    priority_distribution: dict


@app.get("/")
async def root():
    return {
        "message": "Brand Reputation Monitor API",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "models_loaded": sentiment_analyzer is not None}


@app.post("/api/analyze")
async def analyze_reviews(request: MonitoringRequest) -> MonitoringResponse:
    """
    Analyze user-provided reviews
    
    Args:
        request: MonitoringRequest with brand_name and reviews_text
        
    Returns:
        MonitoringResponse with analyzed reviews
    """
    
    if not request.brand_name or len(request.brand_name) < 1:
        raise HTTPException(status_code=400, detail="請輸入品牌名稱")
    
    if sentiment_analyzer is None or problem_classifier is None:
        raise HTTPException(status_code=503, detail="NLP 模型未初始化")
    
    try:
        # Step 1: Scrape Google search results using SerpAPI
        print(f"\n[1/3] Google 搜尋: {request.brand_name}")
        
        api_key = os.getenv("SERPAPI_KEY") or "92534fddc4317ad9fd438f9209b2ac3a67c5f8d393bb8bb6c1d0257111191641"
        if not api_key:
            raise HTTPException(status_code=500, detail="SerpAPI 密鑰未設定")
        
        print(f"  使用 API Key: {api_key[:10]}...")
        
        scraper = SerpAPIScraper(brand_name=request.brand_name, api_key=api_key)
        reviews = await scraper.scrape()
        
        print(f"✓ 找到 {len(reviews)} 篇搜尋結果")
        
        if not reviews:
            return MonitoringResponse(
                brand_name=request.brand_name,
                total_reviews=0,
                reviews=[],
                sentiment_distribution={},
                priority_distribution={}
            )
        
        # Step 2: Analyze sentiment and classify
        print(f"[2/3] 分析情感和分類...")
        analyzed_reviews: List[ReviewAnalysis] = []
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0, "suggestion": 0}
        priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for review in reviews:
            # Analyze sentiment
            sentiment_result = sentiment_analyzer.analyze(review.content)
            
            # Classify category
            classification_result = problem_classifier.classify(review.content)
            
            # Use priority from sentiment analysis (already calculated)
            priority = sentiment_result.priority
            
            # Count sentiments and priorities
            sentiment_counts[sentiment_result.sentiment] += 1
            priority_counts[priority] += 1
            
            # Create analysis object
            analysis = ReviewAnalysis(
                title="",
                content=review.content[:300],
                source="user_input",
                url="",
                sentiment=sentiment_result.sentiment,
                sentiment_score=sentiment_result.score,
                sentiment_confidence=sentiment_result.confidence,
                category=classification_result.category,
                priority=priority,
                keywords=sentiment_result.keywords,
            )
            
            analyzed_reviews.append(analysis)
        
        print(f"✓ 已分析 {len(analyzed_reviews)} 篇評論")
        
        # Step 3: Sort by priority
        print(f"[3/3] 按優先級排序...")
        analyzed_reviews.sort(key=lambda x: x.priority)
        
        return MonitoringResponse(
            brand_name=request.brand_name,
            total_reviews=len(analyzed_reviews),
            reviews=analyzed_reviews,
            sentiment_distribution=sentiment_counts,
            priority_distribution=priority_counts
        )
        
    except Exception as e:
        print(f"分析評論時出錯: {e}")
        raise HTTPException(status_code=500, detail=f"錯誤: {str(e)}")


@app.get("/api/test")
async def test_endpoint():
    """Quick test endpoint"""
    return {
        "test": "working",
        "sentiment_analyzer": sentiment_analyzer is not None,
        "problem_classifier": problem_classifier is not None
    }


def _calculate_priority(sentiment_result: SentimentResult, classification_result) -> int:
    """
    Calculate priority (1 = highest, 5 = lowest)
    Logic:
    - Negative + high confidence = 1 (highest)
    - Suggestion = 2
    - Neutral = 3
    - Positive = 4-5 (lowest)
    """
    
    if sentiment_result.sentiment == "negative":
        # Higher confidence = higher priority
        if sentiment_result.confidence > 0.8:
            return 1
        elif sentiment_result.confidence > 0.6:
            return 2
        else:
            return 3
    
    elif sentiment_result.sentiment == "suggestion":
        return 2
    
    elif sentiment_result.sentiment == "neutral":
        return 3
    
    else:  # positive
        if sentiment_result.confidence > 0.8:
            return 5  # Lowest priority
        else:
            return 4


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
