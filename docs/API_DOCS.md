# API Documentation

## Base URL

```
http://localhost:8000
```

## Endpoints (TODO: Implement)

### Health Check

```
GET /health
```

Response:
```json
{
  "status": "healthy"
}
```

### Create Monitoring Task

```
POST /api/monitoring/start
```

Request:
```json
{
  "brand_name": "example_brand",
  "url": "https://example.com",
  "platforms": ["google_search", "dcard", "ptt", "threads", "instagram"]
}
```

Response:
```json
{
  "task_id": "uuid",
  "status": "started",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Get Reviews with Analysis

```
GET /api/reviews?task_id=<uuid>&sentiment=negative&sort=priority
```

Query Parameters:
- `task_id`: Monitoring task ID (required)
- `sentiment`: Filter by sentiment (optional: positive, negative, neutral, suggestion)
- `category`: Filter by category (optional: logistics, quality, features, price, service)
- `sort`: Sort by field (optional: priority, date, sentiment_score)
- `limit`: Results per page (default: 20)
- `offset`: Pagination offset (default: 0)

Response:
```json
{
  "total": 150,
  "reviews": [
    {
      "id": 1,
      "source": "dcard",
      "title": "Great product!",
      "content": "Really satisfied with the quality...",
      "author": "user123",
      "rating": 5.0,
      "sentiment": "positive",
      "sentiment_score": 0.95,
      "category": "quality",
      "priority": 5,
      "url": "https://...",
      "posted_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

### Generate Response

```
POST /api/reviews/{review_id}/generate-response
```

Request:
```json
{
  "tone": "professional"
}
```

Response:
```json
{
  "review_id": 1,
  "suggested_response": "Thank you for your feedback. We appreciate...",
  "template_used": "template_123"
}
```

### Publish Response

```
POST /api/reviews/{review_id}/publish-response
```

Request:
```json
{
  "response_id": 123,
  "publish_to": "dcard"
}
```

Response:
```json
{
  "status": "published",
  "published_at": "2024-01-01T12:00:00Z",
  "url": "https://..."
}
```

### Get Dashboard Stats

```
GET /api/dashboard/stats?brand_id=<int>
```

Response:
```json
{
  "total_reviews": 1500,
  "sentiment_distribution": {
    "positive": 800,
    "negative": 300,
    "neutral": 300,
    "suggestion": 100
  },
  "platform_distribution": {
    "google_search": 500,
    "dcard": 400,
    "ptt": 300,
    "threads": 200,
    "instagram": 100
  },
  "category_distribution": {
    "quality": 400,
    "logistics": 300,
    "features": 250,
    "service": 300,
    "price": 150,
    "other": 100
  },
  "priority_queue": {
    "high": 50,
    "medium": 150,
    "low": 500
  }
}
```

## Response Status Codes

- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limited
- `500 Internal Server Error`: Server error

## Authentication

_(TODO: Implement)_

## Rate Limiting

_(TODO: Implement)_

## WebSocket Events

_(TODO: Implement real-time updates)_

```
ws://localhost:8000/ws/monitoring/{task_id}
```

Events:
- `review_scraped`: New review found
- `analysis_complete`: Review analyzed
- `response_generated`: Response created
