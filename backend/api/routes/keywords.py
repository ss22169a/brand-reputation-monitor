"""
Keyword Maintenance API for FastAPI
Manages vocabulary database for sentiment analysis, response templates, and issue classification
"""

from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
import json
from datetime import datetime
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter(prefix="/api/keywords", tags=["keywords"])

# Path to keywords.json
KEYWORDS_PATH = Path(__file__).parent.parent.parent / 'data' / 'keywords.json'


class KeywordRequest(BaseModel):
    """Request to add/update/delete keyword"""
    category: str
    word: str
    weight: float = 1.0


class MoveKeywordRequest(BaseModel):
    """Request to move keyword between categories"""
    from_category: str
    to_category: str
    word: str
    weight: float = 1.0


def load_keywords() -> Dict[str, Any]:
    """Load keywords from JSON file"""
    if not KEYWORDS_PATH.exists():
        return {}
    try:
        with open(KEYWORDS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading keywords: {e}")
        return {}


def save_keywords(data: Dict[str, Any]) -> bool:
    """Save keywords to JSON file"""
    try:
        KEYWORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data['metadata']['lastUpdated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(KEYWORDS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving keywords: {e}")
        return False


def sync_to_python_config() -> bool:
    """Sync JSON keywords back to Python config file"""
    try:
        keywords = load_keywords()
        config_path = Path(__file__).parent.parent / 'nlp' / 'keywords_config.py'
        
        if not config_path.exists():
            return False
        
        # Generate Python code
        python_code = '''"""
Keyword Configuration for 4-Level Priority Classification
定期審查並更新（每月 1 次推薦）

Last Updated: {timestamp}
Maintainer: {maintainer}
AUTO-GENERATED - Edit via keywords_admin.html instead
"""

'''.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            maintainer=keywords.get('metadata', {}).get('maintainer', 'Sylvia Ho')
        )
        
        # Add each category
        for category in ['CRITICAL', 'STRATEGIC', 'OPERATIONAL', 'OPPORTUNITIES']:
            if category in keywords:
                cat_data = keywords[category]
                cat_var = category + '_KEYWORDS'
                python_code += f'{cat_var} = {{\n'
                for word, weight in cat_data['keywords'].items():
                    python_code += f'    "{word}": {weight},\n'
                python_code += '}\n\n'
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(python_code)
        
        return True
    except Exception as e:
        print(f"Error syncing to config: {e}")
        return False


# Routes

@router.get("/all")
async def get_all_keywords():
    """Get all keywords by category"""
    keywords = load_keywords()
    return keywords


@router.get("/category/{category}")
async def get_category(category: str):
    """Get keywords for specific category"""
    keywords = load_keywords()
    category_upper = category.upper()
    
    if category_upper not in keywords:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return keywords[category_upper]


@router.get("/search")
async def search_keywords(q: str = Query(..., min_length=1)):
    """Search for keyword across all categories"""
    keywords = load_keywords()
    results = {}
    
    for category, data in keywords.items():
        if category == 'metadata':
            continue
        matches = {k: v for k, v in data.get('keywords', {}).items() if q in k}
        if matches:
            results[category] = {
                'description': data.get('description', ''),
                'keywords': matches
            }
    
    return results


@router.post("/add")
async def add_keyword(request: KeywordRequest):
    """Add new keyword to a category"""
    category = request.category.upper()
    word = request.word.strip()
    weight = float(request.weight)
    
    if not category or not word:
        raise HTTPException(status_code=400, detail="Category and word are required")
    
    keywords = load_keywords()
    
    if category not in keywords:
        raise HTTPException(status_code=404, detail=f"Category {category} not found")
    
    if word in keywords[category]['keywords']:
        raise HTTPException(status_code=409, detail=f'Keyword "{word}" already exists in {category}')
    
    keywords[category]['keywords'][word] = weight
    
    if not save_keywords(keywords):
        raise HTTPException(status_code=500, detail="Error saving keyword")
    
    # Try to sync but don't fail if sync fails
    sync_to_python_config()
    
    return {
        'message': 'Keyword added successfully',
        'category': category,
        'word': word,
        'weight': weight
    }


@router.post("/update")
async def update_keyword(request: KeywordRequest):
    """Update existing keyword"""
    category = request.category.upper()
    word = request.word.strip()
    weight = float(request.weight)
    
    if not category or not word:
        raise HTTPException(status_code=400, detail="Category and word are required")
    
    keywords = load_keywords()
    
    if category not in keywords or word not in keywords[category]['keywords']:
        raise HTTPException(status_code=404, detail=f'Keyword "{word}" not found in {category}')
    
    keywords[category]['keywords'][word] = weight
    
    if not save_keywords(keywords):
        raise HTTPException(status_code=500, detail="Error updating keyword")
    
    # Try to sync but don't fail if sync fails
    sync_to_python_config()
    
    return {
        'message': 'Keyword updated successfully',
        'category': category,
        'word': word,
        'weight': weight
    }


@router.post("/delete")
async def delete_keyword(request: KeywordRequest):
    """Delete keyword from category"""
    category = request.category.upper()
    word = request.word.strip()
    
    if not category or not word:
        raise HTTPException(status_code=400, detail="Category and word are required")
    
    keywords = load_keywords()
    
    if category not in keywords or word not in keywords[category]['keywords']:
        raise HTTPException(status_code=404, detail=f'Keyword "{word}" not found in {category}')
    
    del keywords[category]['keywords'][word]
    
    if not save_keywords(keywords):
        raise HTTPException(status_code=500, detail="Error deleting keyword")
    
    # Try to sync but don't fail if sync fails
    sync_to_python_config()
    
    return {
        'message': 'Keyword deleted successfully',
        'category': category,
        'word': word
    }


@router.post("/move")
async def move_keyword(request: MoveKeywordRequest):
    """Move keyword from one category to another"""
    from_category = request.from_category.upper()
    to_category = request.to_category.upper()
    word = request.word.strip()
    weight = float(request.weight)
    
    if not from_category or not to_category or not word:
        raise HTTPException(status_code=400, detail="from_category, to_category, and word are required")
    
    keywords = load_keywords()
    
    if from_category not in keywords or word not in keywords[from_category]['keywords']:
        raise HTTPException(status_code=404, detail=f'Keyword "{word}" not found in {from_category}')
    
    if to_category not in keywords:
        raise HTTPException(status_code=404, detail=f"Category {to_category} not found")
    
    # Delete from old category
    del keywords[from_category]['keywords'][word]
    # Add to new category
    keywords[to_category]['keywords'][word] = weight
    
    if not save_keywords(keywords):
        raise HTTPException(status_code=500, detail="Error moving keyword")
    
    # Try to sync but don't fail if sync fails
    sync_to_python_config()
    
    return {
        'message': f'Keyword moved from {from_category} to {to_category}',
        'word': word,
        'weight': weight
    }


@router.get("/stats")
async def get_stats():
    """Get statistics about the vocabulary"""
    keywords = load_keywords()
    stats = {}
    total_keywords = 0
    
    for category in ['CRITICAL', 'STRATEGIC', 'OPERATIONAL', 'OPPORTUNITIES']:
        if category in keywords:
            count = len(keywords[category]['keywords'])
            stats[category] = count
            total_keywords += count
    
    stats['TOTAL'] = total_keywords
    stats['lastUpdated'] = keywords.get('metadata', {}).get('lastUpdated', 'Unknown')
    
    return stats
