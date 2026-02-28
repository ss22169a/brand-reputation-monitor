"""
Sentiment analysis for Traditional Chinese reviews
Uses BERT-based model for Chinese text
"""
from dataclasses import dataclass, field
from typing import Literal
import torch
from transformers import pipeline


@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    text: str
    sentiment: Literal["positive", "negative", "neutral", "suggestion"]
    score: float  # 0.0 - 1.0
    keywords: list[str] = field(default_factory=list)
    confidence: float = 0.0


class SentimentAnalyzer:
    """
    Analyze sentiment of Chinese reviews using BERT
    """
    
    def __init__(self, use_ml: bool = False):
        self.model_name = "bert-base-chinese"
        self.use_ml = use_ml
        self.classifier = None
        
        # ML model disabled by default - use rule-based for speed
        # Uncomment if you want to use BERT-based classification
        # if use_ml:
        #     try:
        #         self.classifier = pipeline(
        #             "zero-shot-classification",
        #             model=self.model_name,
        #             device=0 if torch.cuda.is_available() else -1
        #         )
        #     except Exception as e:
        #         print(f"Warning: Could not load classifier: {e}")
        #         self.classifier = None
        
        # Keywords for simple fallback analysis
        self.positive_keywords = {
            "好": 2, "棒": 2, "讚": 2, "優": 1, "完美": 2,
            "滿意": 1.5, "喜歡": 1, "推薦": 1.5, "愛": 1,
            "很好": 1.5, "不錯": 1, "贊": 1.5, "開心": 1,
            "超讚": 2, "完美無缺": 2,
        }
        
        self.negative_keywords = {
            "爛": 2, "糟": 2, "差": 1.5, "不好": 1, "討厭": 2,
            "失望": 1.5, "問題": 1, "缺點": 1, "有問題": 1.5,
            "不滿": 1.5, "壞": 1.5, "垃圾": 2, "爛透": 2,
            "後悔": 2, "浪費": 1.5, "騙": 2,
        }
        
        self.suggestion_keywords = {
            "建議": 1, "希望": 0.8, "可以": 0.5, "應該": 0.8,
            "需要": 0.7, "改進": 1, "改善": 1, "優化": 1,
            "如果": 0.5, "最好": 0.8,
        }
        
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
        
        # Score suggestion keywords
        for keyword, weight in self.suggestion_keywords.items():
            if keyword in text:
                suggestion_score += weight
        
        # Determine sentiment
        total_score = positive_score + negative_score + suggestion_score
        
        if total_score == 0:
            sentiment = "neutral"
            score = 0.5
            confidence = 0.3
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
            confidence=min(confidence, 0.95)
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
