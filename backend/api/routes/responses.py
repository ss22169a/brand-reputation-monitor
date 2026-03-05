"""
Auto Response Suggestion API
Provides intelligent response templates based on priority and sentiment classification
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from datetime import datetime
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter(prefix="/api/responses", tags=["responses"])

# Path to response templates
RESPONSES_PATH = Path(__file__).parent.parent.parent / 'data' / 'response_templates.json'


class ResponseRequest(BaseModel):
    """Request for auto response suggestion"""
    priority: int  # 1-5
    sentiment: str  # positive, negative, neutral, suggestion
    category: Optional[str] = None  # quality, service, fraud, etc.
    content: Optional[str] = None  # Review content for context


def load_responses() -> Dict[str, Any]:
    """Load response templates from JSON"""
    if not RESPONSES_PATH.exists():
        return {}
    try:
        with open(RESPONSES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading responses: {e}")
        return {}


def save_responses(data: Dict[str, Any]) -> bool:
    """Save response templates"""
    try:
        RESPONSES_PATH.parent.mkdir(parents=True, exist_ok=True)
        data['metadata']['lastUpdated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(RESPONSES_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving responses: {e}")
        return False


def get_priority_label(priority: int) -> str:
    """Convert priority int to category label"""
    priority_map = {
        1: 'CRITICAL',
        2: 'STRATEGIC',
        3: 'OPERATIONAL',
        4: 'OPPORTUNITIES',
        5: 'NEUTRAL'
    }
    return priority_map.get(priority, 'NEUTRAL')


@router.post("/suggest")
async def suggest_response(request: ResponseRequest):
    """
    Get suggested auto response based on priority and category
    
    Example:
    {
        "priority": 1,
        "sentiment": "negative",
        "category": "quality"
    }
    """
    responses = load_responses()
    priority_label = get_priority_label(request.priority)
    
    if priority_label not in responses:
        raise HTTPException(status_code=404, detail=f"No responses for {priority_label}")
    
    priority_responses = responses[priority_label]
    
    # Try to get specific category response
    if request.category and request.category in priority_responses:
        suggested = priority_responses[request.category]
    else:
        # Fall back to default
        suggested = priority_responses.get('default', '感謝您的反饋，我們會持續改進。')
    
    return {
        'priority': request.priority,
        'priority_label': priority_label,
        'sentiment': request.sentiment,
        'category': request.category,
        'suggested_response': suggested,
        'editable': True
    }


@router.get("/all")
async def get_all_responses():
    """Get all response templates"""
    return load_responses()


@router.get("/category/{priority}/{category}")
async def get_response_by_category(priority: int, category: str):
    """Get response for specific priority and category"""
    responses = load_responses()
    priority_label = get_priority_label(priority)
    
    if priority_label not in responses:
        raise HTTPException(status_code=404, detail=f"Priority {priority} not found")
    
    if category not in responses[priority_label]:
        raise HTTPException(status_code=404, detail=f"Category {category} not found")
    
    return {
        'priority': priority,
        'category': category,
        'response': responses[priority_label][category]
    }


@router.post("/update")
async def update_response(priority: int, category: str, new_text: str):
    """Update response template"""
    responses = load_responses()
    priority_label = get_priority_label(priority)
    
    if priority_label not in responses:
        raise HTTPException(status_code=404, detail=f"Priority {priority} not found")
    
    responses[priority_label][category] = new_text
    
    if not save_responses(responses):
        raise HTTPException(status_code=500, detail="Error saving response")
    
    return {
        'message': 'Response updated',
        'priority': priority_label,
        'category': category,
        'response': new_text
    }
