"""
Keyword library for brand monitoring
Stores common complaint/review terms for different categories
"""

# Problem keywords (what people complain about)
PROBLEM_KEYWORDS = {
    "quality": ["品質差", "品質爛", "材質差", "材質爛", "破損", "缺陷", "瑕疵", "易壞", "不耐用", "掉色", "褪色"],
    "price": ["太貴", "價格高", "不值", "貴死了", "CP值低", "性價比差", "搶錢", "黑心"],
    "shipping": ["運費貴", "配送慢", "物流爛", "寄丟", "寄壞", "發貨慢", "速度慢"],
    "service": ["客服爛", "客服差", "沒人理", "態度差", "愛理不理", "售後爛", "不負責", "退貨難"],
    "fraud": ["抄襲", "假貨", "仿冒", "詐騙", "虛假宣傳", "誤導", "描述不符", "貨不對板"],
    "design": ["設計差", "醜", "山寨", "沒創意", "仿造", "抄襲"],
    "other": ["後悔", "不推薦", "踩雷", "避坑", "黑名單", "絕不再買"],
}

# Positive keywords
POSITIVE_KEYWORDS = [
    "品質好", "材質好", "很新穎", "設計好", "喜歡", "推薦", "值得", "滿意", "讚",
    "物超所值", "CP值高", "服務好", "客服棒", "配送快", "包裝精美", "不錯",
    "愛上", "必買", "再買", "朋友", "姐妹",
]

# Negative keywords (for filtering posts)
NEGATIVE_KEYWORDS = [
    "爛", "差", "垃圾", "黑心", "詐騙", "騙", "虛假", "假貨", "仿冒", "抄襲",
    "後悔", "踩雷", "避坑", "失望", "不推薦",
]

# Platforms and their search strategies
PLATFORM_STRATEGIES = {
    "dcard": {
        "forums": ["all", "recommend", "shopping", "bargain"],
        "search_keywords": list(PROBLEM_KEYWORDS.values()),  # Use problem keywords, not brand name
        "description": "台灣大學社群平台，用戶會詳細討論商品問題"
    },
    "ptt": {
        "boards": ["Gossiping", "MobileComm", "Shopping"],
        "search_keywords": list(PROBLEM_KEYWORDS.values()),
        "description": "台灣論壇，使用者會詳細評論和討論"
    },
    "threads": {
        "search_type": "hashtag",
        "description": "Meta 社群平台，用 hashtag 搜尋"
    },
    "instagram": {
        "search_type": "hashtag",
        "description": "圖片社群，用 hashtag 搜尋"
    },
    "google_search": {
        "search_strategy": "brand_name + negative_keywords",
        "description": "搜尋引擎，結合品牌名 + 負面詞"
    }
}


def get_search_keywords_for_brand(brand_name: str) -> dict:
    """
    Generate search keywords for a brand
    Returns: {
        'primary': [keywords to search],
        'filter': [keywords to filter results],
        'platforms': {platform: strategy}
    }
    """
    return {
        "brand_name": brand_name,
        "problem_keywords": list(PROBLEM_KEYWORDS.values()),  # All problem categories
        "positive_keywords": POSITIVE_KEYWORDS,
        "negative_keywords": NEGATIVE_KEYWORDS,
        "platforms": PLATFORM_STRATEGIES,
        "instructions": {
            "dcard": f"搜尋: 品牌名「{brand_name}」+問題詞彙（品質差、抄襲、太貴等），而不是單獨搜品牌名",
            "instagram": f"搜尋 hashtag: #{brand_name} 或 #品牌相關詞，然後提取每篇貼文",
            "ptt": f"在八卦版搜尋「{brand_name}」相關文章，過濾負面評論",
            "threads": f"搜尋 hashtag #{brand_name}，提取貼文內容",
        }
    }


def categorize_by_keyword(text: str) -> str:
    """
    Categorize text by dominant problem keyword
    Returns: category name
    """
    text_lower = text.lower()
    
    for category, keywords in PROBLEM_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    
    return "other"


def extract_problem_keywords(text: str) -> list:
    """Extract all problem keywords found in text"""
    text_lower = text.lower()
    found_keywords = []
    
    for category, keywords in PROBLEM_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower and keyword not in found_keywords:
                found_keywords.append(keyword)
    
    return found_keywords


if __name__ == "__main__":
    # Test
    brand = "BLANK SPACE"
    keywords = get_search_keywords_for_brand(brand)
    
    print(f"品牌: {brand}")
    print(f"\n搜尋策略:")
    for platform, instructions in keywords["instructions"].items():
        print(f"  {platform}: {instructions}")
    
    # Test categorization
    test_text = "這個品牌的材質很爛，品質差，太貴了，客服也不好"
    print(f"\n測試文本: {test_text}")
    print(f"分類: {categorize_by_keyword(test_text)}")
    print(f"關鍵詞: {extract_problem_keywords(test_text)}")
