"""
Sentiment analysis for Traditional Chinese reviews
Uses BERT-based model for Chinese text
"""
from dataclasses import dataclass, field
from typing import Literal

# Optional imports - make torch and transformers optional
try:
    import torch
    from transformers import pipeline
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    text: str
    sentiment: Literal["positive", "negative", "neutral", "suggestion"]
    score: float  # 0.0 - 1.0
    keywords: list[str] = field(default_factory=list)
    confidence: float = 0.0
    priority: int = 4  # 1=Critical, 2=Strategic, 3=Operational, 4=Opportunities, 5=neutral
    category: str = "neutral"  # critical, strategic, operational, opportunity


class SentimentAnalyzer:
    """
    Analyze sentiment of Chinese reviews using BERT
    """
    
    def __init__(self, use_ml: bool = False):
        self.model_name = "bert-base-chinese"
        self.use_ml = use_ml
        self.classifier = None
        
        # Initialize keywords with defaults
        self.positive_keywords = {"好": 2, "棒": 2, "讚": 2, "優": 1}
        self.negative_keywords = {"爛": 2, "糟": 2, "垃圾": 2, "討厭": 2}
        self.suggestion_keywords = {"建議": 1, "希望": 0.8}
        self.critical_keywords = {}
        self.strategic_keywords = {}
        self.operational_keywords = {}
        self.opportunity_keywords = {}
        
        # Load keywords from JSON file
        self._load_keywords_from_json()
        
        # ML model disabled by default - use rule-based for speed
        if use_ml and HAS_TORCH:
            try:
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model=self.model_name,
                    device=0 if torch.cuda.is_available() else -1
                )
            except Exception as e:
                print(f"Warning: Could not load classifier: {e}")
                self.classifier = None
    
    def _load_keywords_from_json(self) -> None:
        """Load keywords from JSON file with better error handling"""
        import json
        from pathlib import Path
        
        # Try multiple paths
        possible_paths = [
            Path(__file__).parent.parent / 'data' / 'keywords.json',
            Path.cwd() / 'backend' / 'data' / 'keywords.json',
            Path.cwd() / 'data' / 'keywords.json',
        ]
        
        json_path = None
        for path in possible_paths:
            if path.exists():
                json_path = path
                break
        
        if not json_path:
            print(f"⚠️ 找不到 keywords.json")
            return
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load each category
            self.critical_keywords = dict(data.get('CRITICAL', {}).get('keywords', {}))
            self.strategic_keywords = dict(data.get('STRATEGIC', {}).get('keywords', {}))
            self.operational_keywords = dict(data.get('OPERATIONAL', {}).get('keywords', {}))
            self.opportunity_keywords = dict(data.get('OPPORTUNITIES', {}).get('keywords', {}))
            
            total = (len(self.critical_keywords) + len(self.strategic_keywords) + 
                    len(self.operational_keywords) + len(self.opportunity_keywords))
            
            print(f"✓ 已從 keywords.json 載入 {total} 個詞彙")
            
        except Exception as e:
            print(f"⚠️ 載入詞彙失敗: {e}")
        
    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of review text
        
        Args:
            text: Review content (Chinese)
            
        Returns:
            SentimentResult with sentiment, score, and keywords
        """
        if not text or len(text) < 2:
            return SentimentResult(
                text=text,
                sentiment="neutral",
                score=0.5,
                keywords=[],
                confidence=0.0
            )
        
        # Try ML-based analysis first
        if self.classifier:
            try:
                result = self._ml_analyze(text)
                if result:
                    return result
            except Exception as e:
                print(f"ML analysis failed: {e}, falling back to rule-based")
        
        # Fallback to rule-based analysis
        return self._rule_based_analyze(text)
    
    def _ml_analyze(self, text: str) -> SentimentResult | None:
        """Use ML model for sentiment analysis"""
        try:
            candidate_labels = ["正面", "負面", "建議", "中立"]
            result = self.classifier(text, candidate_labels)
            
            label = result['labels'][0]
            score = result['scores'][0]
            
            # Map labels to sentiment types
            sentiment_map = {
                "正面": "positive",
                "負面": "negative",
                "建議": "suggestion",
                "中立": "neutral"
            }
            
            return SentimentResult(
                text=text,
                sentiment=sentiment_map.get(label, "neutral"),
                score=score,
                keywords=[label],
                confidence=score
            )
        except Exception as e:
            print(f"ML analysis error: {e}")
            return None
    
    def _rule_based_analyze(self, text: str) -> SentimentResult:
        """Rule-based sentiment analysis using keywords"""
        positive_score = 0.0
        negative_score = 0.0
        suggestion_score = 0.0
        found_keywords = []
        has_strong_negative = False
        
        # 4 級優先級計分
        critical_score = 0.0
        strategic_score = 0.0
        operational_score = 0.0
        opportunity_score = 0.0
        
        text_lower = text.lower()
        
        # Score positive keywords
        for keyword, weight in self.positive_keywords.items():
            if keyword in text:
                positive_score += weight
                found_keywords.append(f"+{keyword}")
        
        # Score negative keywords
        for keyword, weight in self.negative_keywords.items():
            if keyword in text:
                negative_score += weight
                found_keywords.append(f"-{keyword}")
                if weight >= 2:
                    has_strong_negative = True
        
        # Score suggestion keywords
        for keyword, weight in self.suggestion_keywords.items():
            if keyword in text:
                suggestion_score += weight
        
        # 計分 4 級優先級
        for keyword, weight in self.critical_keywords.items():
            if keyword in text:
                critical_score += weight
                
        for keyword, weight in self.strategic_keywords.items():
            if keyword in text:
                strategic_score += weight
                
        for keyword, weight in self.operational_keywords.items():
            if keyword in text:
                operational_score += weight
                
        for keyword, weight in self.opportunity_keywords.items():
            if keyword in text:
                opportunity_score += weight
        
        # Determine sentiment
        total_score = positive_score + negative_score + suggestion_score
        
        # 決定 4 級優先級
        priority = 5  # Default: neutral
        category = "neutral"
        
        if critical_score > 0:
            priority = 1
            category = "critical"
        elif strategic_score > 0:
            priority = 2
            category = "strategic"
        elif operational_score > 0:
            priority = 3
            category = "operational"
        elif opportunity_score > 0:
            priority = 4
            category = "opportunity"
        
        if total_score == 0:
            sentiment = "neutral"
            score = 0.5
            confidence = 0.3
        # 如果有强烈负面词（权重 >= 2），直接判为负面（防止"开头正面+后面批评"的问题）
        elif has_strong_negative and negative_score >= positive_score * 0.5:
            sentiment = "negative"
            confidence = min(negative_score / max(total_score, 1), 0.95)
            score = max(0.05, 0.5 - (negative_score / 10))
        elif suggestion_score > positive_score and suggestion_score > negative_score:
            sentiment = "suggestion"
            confidence = suggestion_score / max(total_score, 1)
            score = 0.6
        elif positive_score > negative_score:
            sentiment = "positive"
            confidence = positive_score / max(total_score, 1)
            score = min(0.95, 0.5 + (positive_score / 10))
        elif negative_score > positive_score:
            sentiment = "negative"
            confidence = negative_score / max(total_score, 1)
            score = max(0.05, 0.5 - (negative_score / 10))
        else:
            sentiment = "neutral"
            score = 0.5
            confidence = 0.4
        
        return SentimentResult(
            text=text,
            sentiment=sentiment,
            score=score,
            keywords=found_keywords[:5],  # Top 5 keywords
            confidence=min(confidence, 0.95),
            priority=priority,
            category=category
        )


# Test function
def test_sentiment_analyzer():
    """Test the sentiment analyzer"""
    analyzer = SentimentAnalyzer()
    
    test_texts = [
        "這個產品真的很棒，我非常滿意！",
        "品質很差，我很失望。",
        "產品還不錯，但希望能改進包裝。",
        "中規中矩的商品。",
        "完全後悔購買，垃圾產品！",
    ]
    
    print("Testing Sentiment Analyzer")
    print("=" * 60)
    
    for text in test_texts:
        result = analyzer.analyze(text)
        print(f"\nText: {text}")
        print(f"  Sentiment: {result.sentiment}")
        print(f"  Score: {result.score:.2f}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Keywords: {result.keywords}")


if __name__ == "__main__":
    test_sentiment_analyzer()
