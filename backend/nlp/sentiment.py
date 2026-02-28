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
        
        # Load keywords from keywords_config.py
        self._load_keywords_from_config()
        
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
            # 强烈负面
            "爛": 2, "糟": 2, "垃圾": 2, "爛透": 2, "討厭": 2,
            "後悔": 2, "騙": 2, "詐騙": 2, "破爛": 2,
            # 中等负面
            "差": 1.5, "不好": 1.5, "失望": 1.5, "有問題": 1.5,
            "不滿": 1.5, "壞": 1.5, "浪費": 1.5, "虧": 1.5,
            "缺陷": 1.5, "故障": 1.5, "壞掉": 1.5,
            # 轻度负面
            "問題": 1, "缺點": 1, "不夠": 1, "不足": 1,
            "過期": 1.2, "損壞": 1.2, "破損": 1.2,
            "沒用": 1.2, "無用": 1.2, "劣質": 1.5,
            # 产品质量问题
            "品質差": 2, "質量差": 2, "品質不好": 1.5,
            "做工差": 1.5, "工藝差": 1.5,
            # 售后问题
            "售後差": 1.5, "服務差": 1.5, "無法退": 1.5,
            "不退貨": 1.5, "不換貨": 1.5,
            # 电池/性能问题
            "電池壞": 2, "電池爆": 2, "發熱": 1.5,
            "續航差": 1.5, "充不進": 1.5, "掉電": 1.5,
            # 其他常见问题
            "噪音": 1.2, "刮傷": 1, "掉漆": 1.2,
            "生鏽": 1.5, "發霉": 1.5, "臭": 1.2,
        }
        
        self.suggestion_keywords = {
            "建議": 1, "希望": 0.8, "可以": 0.5, "應該": 0.8,
            "需要": 0.7, "改進": 1, "改善": 1, "優化": 1,
            "如果": 0.5, "最好": 0.8,
        }
        
        # 4 級優先級分類
        # 1. Critical - 危機警示 (品牌形象受損)
        self.critical_keywords = {
            # 品質質疑 (15詞)
            "壞掉": 2, "爆掉": 2, "故障": 2, "無法使用": 1.5, "損壞": 1.5, "破損": 1.5,
            "瑕疵": 1.5, "缺陷": 1.5, "不堪一用": 2,
            "受騙": 2, "被騙": 2, "詐騙": 2,
            "廣告不實": 2, "虛假宣傳": 2, "名不符實": 2,
            "圖文不符": 2, "實物不符": 2,
            "失望": 1.5, "很失望": 1.5,
            
            # 服務衝突 (16詞)
            "態度差": 1.5, "服務態度差": 1.5, "很囂張": 2, "愛理不理": 1.5,
            "互推責任": 2, "推諉": 2, "踢皮球": 2,
            "等超久": 1.5, "等很久": 1.5, "一直等": 1.5, "客服慢": 1.5,
            "投訴": 1.5, "申訴": 1.5, "客訴": 1.5,
            "消保官": 2, "檢舉": 1.5, "曝光": 1.5,
            "公審": 2, "網路審判": 2, "被罵爆": 2,
            
            # 品牌誠信 (14詞)
            "收割": 2, "收割韭菜": 2, "割一波": 2,
            "割韭菜": 2, "韭菜": 1.5,
            "公關災難": 2, "公關翻車": 2,
            "炎上": 2, "燒起來": 2, "被炎上": 2,
            "翻車": 2, "大翻車": 2,
            "雙標": 2, "雙標仔": 2,
        }
        
        # 2. Strategic - 情感轉向 (品牌忠誠度下滑) 24詞
        self.strategic_keywords = {
            # 比較競爭 (10詞)
            "以前比較好": 1.5, "以前更好": 1.5, "隔壁棚更好": 1.5, "比其他牌": 1.5, "對比之下": 1.5,
            "退步了": 1.5, "越來越差": 1.5, "變貴了": 1.5, "價格上升": 1.5, "CP值變低": 1.5,
            
            # 替代選擇 (8詞)
            "有沒有推薦別家": 1.5, "推薦替代": 1.5, "換品牌": 1.5, "轉向": 1.5,
            "跳槽": 1.5, "轉投": 1.5, "退坑": 1.5, "被推坑別的": 1.5,
            
            # 疲乏感 (6詞)
            "看膩了": 1, "審美疲勞": 1, "沒創意": 1, "又來了": 1, "無感": 1, "一樣套路": 1,
        }
        
        # 3. Operational - 使用痛點 (產品/流程優化) 20詞
        self.operational_keywords = {
            # 介面/流程 (12詞)
            "找不到": 1, "卡住": 1, "卡頓": 1, "很難用": 1, "操作複雜": 1, "跳掉": 1,
            "註冊不了": 1, "無法登入": 1, "驗證碼沒收過": 1, "驗證失敗": 1, "流程繁瑣": 1, "一直出錯": 1,
            
            # 資訊落差 (8詞)
            "看不懂": 1, "到底在哪裡": 1, "文字不清楚": 1, "說明不足": 1,
            "沒人回": 1.5, "沒有客服": 1.5, "官網沒寫": 1, "找不到說明": 1,
        }
        
        # 4. Opportunities - 關鍵商機 (銷售轉化) 18詞
        self.opportunity_keywords = {
            # 購買意圖 (10詞)
            "求代購": 1, "代購": 1, "哪裡買": 1, "在哪買": 1, "還有貨嗎": 1,
            "敲碗": 1, "搶著要": 1, "期待": 1, "早點出": 1, "想入坑": 1,
            
            # 功能許願 (8詞)
            "希望有": 1, "希望增加": 1, "功能": 0.5, "新色": 1, "色就好了": 1,
            "建議增加": 1, "如果有就好": 1, "期待推出": 1,
        }
    
    def _load_keywords_from_config(self) -> None:
        """Load keywords from keywords_config.py"""
        try:
            # Try to import from keywords_config
            try:
                from keywords_config import (
                    CRITICAL_KEYWORDS,
                    STRATEGIC_KEYWORDS, 
                    OPERATIONAL_KEYWORDS,
                    OPPORTUNITIES_KEYWORDS
                )
            except ImportError:
                # If direct import fails, try relative import
                from .keywords_config import (
                    CRITICAL_KEYWORDS,
                    STRATEGIC_KEYWORDS,
                    OPERATIONAL_KEYWORDS,
                    OPPORTUNITIES_KEYWORDS
                )
            
            # Override the hardcoded keywords with config file values
            if CRITICAL_KEYWORDS:
                self.critical_keywords = CRITICAL_KEYWORDS
            if STRATEGIC_KEYWORDS:
                self.strategic_keywords = STRATEGIC_KEYWORDS
            if OPERATIONAL_KEYWORDS:
                self.operational_keywords = OPERATIONAL_KEYWORDS
            if OPPORTUNITIES_KEYWORDS:
                self.opportunity_keywords = OPPORTUNITIES_KEYWORDS
                
            print("✓ 已從 keywords_config.py 載入詞彙")
            
        except ImportError as e:
            print(f"⚠️ 無法載入 keywords_config.py: {e}，使用預設詞彙")
        except Exception as e:
            print(f"⚠️ 載入詞彙時出錯: {e}，使用預設詞彙")
        
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
