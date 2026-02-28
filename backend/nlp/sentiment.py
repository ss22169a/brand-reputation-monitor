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
        self.positive_keywords = {
            "好": 2, "棒": 2, "讚": 2, "優": 1, "完美": 2,
            "滿意": 1.5, "喜歡": 1, "推薦": 1.5, "愛": 1,
            "很好": 1.5, "不錯": 1, "贊": 1.5, "開心": 1,
            "超讚": 2, "完美無缺": 2,
        }
        self.negative_keywords = {
            "爛": 2, "糟": 2, "垃圾": 2, "爛透": 2, "討厭": 2,
            "後悔": 2, "騙": 2, "詐騙": 2, "破爛": 2,
            "差": 1.5, "很差": 1.5, "差勁": 1.5, "很差勁": 1.5,
            "不好": 1.5, "失望": 1.5, "有問題": 1.5,
            "不滿": 1.5, "壞": 1.5, "浪費": 1.5, "虧": 1.5,
            "缺陷": 1.5, "故障": 1.5, "壞掉": 1.5,
            "問題": 1, "缺點": 1, "不夠": 1, "不足": 1,
            "過期": 1.2, "損壞": 1.2, "破損": 1.2,
            "沒用": 1.2, "無用": 1.2, "劣質": 1.5,
        }
        self.suggestion_keywords = {
            "建議": 1, "希望": 0.8, "可以": 0.5, "應該": 0.8,
            "需要": 0.7, "改進": 1, "改善": 1, "優化": 1,
            "如果": 0.5, "最好": 0.8,
        }
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
        """Rule-based sentiment analysis using 4-level priority keywords
        
        NEW LOGIC (2026-03-01):
        - CRITICAL 詞 → sentiment=negative, priority=1, status=待處理
        - STRATEGIC 詞 → sentiment=根據內容評估, priority=2, status=優化溝通
        - OPERATIONAL 詞 → sentiment=neutral, priority=3, status=產品優化
        - OPPORTUNITIES 詞 → sentiment=positive, priority=4, status=乘勝追擊
        """
        found_keywords = []
        
        # 4 級優先級計分
        critical_score = 0.0
        strategic_score = 0.0
        operational_score = 0.0
        opportunity_score = 0.0
        
        # 計分 4 級優先級
        for keyword, weight in self.critical_keywords.items():
            if keyword in text:
                critical_score += weight
                found_keywords.append(f"CRITICAL:{keyword}")
                
        for keyword, weight in self.strategic_keywords.items():
            if keyword in text:
                strategic_score += weight
                found_keywords.append(f"STRATEGIC:{keyword}")
                
        for keyword, weight in self.operational_keywords.items():
            if keyword in text:
                operational_score += weight
                found_keywords.append(f"OPERATIONAL:{keyword}")
                
        for keyword, weight in self.opportunity_keywords.items():
            if keyword in text:
                opportunity_score += weight
                found_keywords.append(f"OPPORTUNITIES:{keyword}")
        
        # 決定優先級和情感
        priority = 5  # Default: neutral
        category = "neutral"
        sentiment = "neutral"
        score = 0.5
        confidence = 0.3
        
        # 優先級判斷（按優先順序）
        if critical_score > 0:
            priority = 1
            category = "critical"
            sentiment = "negative"  # CRITICAL → 負面
            score = 0.2
            confidence = 0.9
        elif strategic_score > 0:
            priority = 2
            category = "strategic"
            # STRATEGIC 需要評估：跟客服/售後相關詞 → 負面，其他 → 中立
            customer_service_keywords = {"客服", "服務", "售後", "回應", "處理", "態度", "回覆"}
            is_customer_service_issue = any(kw in text for kw in customer_service_keywords)
            sentiment = "negative" if is_customer_service_issue else "neutral"
            score = 0.3 if sentiment == "negative" else 0.5
            confidence = 0.7
        elif operational_score > 0:
            priority = 3
            category = "operational"
            sentiment = "neutral"  # OPERATIONAL → 中立
            score = 0.5
            confidence = 0.6
        elif opportunity_score > 0:
            priority = 4
            category = "opportunity"
            sentiment = "positive"  # OPPORTUNITIES → 正面
            score = 0.8
            confidence = 0.8
        
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
