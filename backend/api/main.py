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

from nlp.sentiment import SentimentAnalyzer, SentimentResult
from nlp.classifier import ProblemClassifier
from scrapers.base import Review
from datetime import datetime

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
    """Request to analyze user-provided reviews"""
    brand_name: str
    reviews_text: str


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
    
    if not request.reviews_text or len(request.reviews_text) < 5:
        raise HTTPException(status_code=400, detail="請輸入評論文本")
    
    if sentiment_analyzer is None or problem_classifier is None:
        raise HTTPException(status_code=503, detail="NLP 模型未初始化")
    
    try:
        # Step 1: Parse user reviews
        print(f"\n[1/3] 解析評論: {request.brand_name}")
        
        # Split by newlines or other delimiters
        review_texts = [
            text.strip() 
            for text in request.reviews_text.split('\n') 
            if text.strip() and len(text.strip()) > 5
        ]
        
        print(f"✓ 找到 {len(review_texts)} 篇評論")
        
        if not review_texts:
            return MonitoringResponse(
                brand_name=request.brand_name,
                total_reviews=0,
                reviews=[],
                sentiment_distribution={},
                priority_distribution={}
            )
        
        # Convert to Review objects
        reviews = [
            Review(
                source="user_input",
                title="",
                content=text,
                author="用戶",
                rating=None,
                url="",
                scraped_at=datetime.now(),
                posted_at=None,
            )
            for text in review_texts
        ]
        
        # Step 2: Analyze sentiment and classify
        print(f"[2/3] 分析情感和分類...")
        analyzed_reviews: List[ReviewAnalysis] = []
        sentiment_counts = {"positive": 0, "negative": 0, "suggestion": 0}
        priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for review in reviews:
            # Analyze sentiment
            sentiment_result = sentiment_analyzer.analyze(review.content)
            
            # Classify category
            classification_result = problem_classifier.classify(review.content)
            
            # Calculate priority (1 = highest, 5 = lowest)
            priority = _calculate_priority(sentiment_result, classification_result)
            
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
