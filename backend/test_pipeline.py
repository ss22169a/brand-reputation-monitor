"""
End-to-end test: Scrape -> Analyze Sentiment -> Classify
"""
import asyncio
from scrapers.google_search import GoogleSearchScraper
from nlp.sentiment import SentimentAnalyzer
from nlp.classifier import ProblemClassifier


async def test_full_pipeline():
    """Test the complete pipeline"""
    
    # Configuration
    brand_name = "iPhone"
    
    print("=" * 70)
    print("BRAND REPUTATION MONITORING PIPELINE TEST")
    print("=" * 70)
    print(f"\nBrand: {brand_name}")
    print("-" * 70)
    
    # Step 1: Scrape reviews
    print("\n[STEP 1] Scraping reviews from Google Search...")
    scraper = GoogleSearchScraper(brand_name=brand_name)
    reviews = await scraper.scrape()
    
    print(f"✓ Found {len(reviews)} results")
    
    # Step 2: Analyze sentiment
    print("\n[STEP 2] Analyzing sentiment...")
    sentiment_analyzer = SentimentAnalyzer()
    classifier = ProblemClassifier()
    
    results = []
    for i, review in enumerate(reviews[:10], 1):  # Limit to first 10 for demo
        print(f"\nResult {i}: {review.title[:50]}...")
        
        # Analyze sentiment
        sentiment = sentiment_analyzer.analyze(review.content)
        print(f"  Sentiment: {sentiment.sentiment} (score: {sentiment.score:.2f})")
        print(f"  Confidence: {sentiment.confidence:.2f}")
        print(f"  Keywords: {sentiment.keywords}")
        
        # Classify problem
        classification = classifier.classify(review.content)
        print(f"  Category: {classification.category}")
        
        # Calculate priority (simple formula)
        # Negative + high confidence = high priority
        priority = 1
        if sentiment.sentiment == "negative":
            priority = 1  # High priority
        elif sentiment.sentiment == "suggestion":
            priority = 2  # Medium priority
        elif sentiment.sentiment == "neutral":
            priority = 3
        else:  # positive
            priority = 4  # Low priority
        
        print(f"  Priority: {priority}")
        
        results.append({
            "review": review,
            "sentiment": sentiment,
            "classification": classification,
            "priority": priority
        })
    
    # Step 3: Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    sentiments = [r["sentiment"].sentiment for r in results]
    sentiment_count = {
        "positive": sentiments.count("positive"),
        "negative": sentiments.count("negative"),
        "neutral": sentiments.count("neutral"),
        "suggestion": sentiments.count("suggestion"),
    }
    
    print("\nSentiment Distribution:")
    for sentiment, count in sentiment_count.items():
        print(f"  {sentiment}: {count}")
    
    print("\nHigh Priority (Negative) Reviews:")
    high_priority = [r for r in results if r["priority"] == 1]
    if high_priority:
        for r in high_priority:
            print(f"  - {r['review'].title[:50]}...")
    else:
        print("  (None)")
    
    print("\n✓ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
