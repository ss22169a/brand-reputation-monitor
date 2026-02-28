# Architecture Overview

## System Design

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐     │
│  │ Input Panel  │  │ Dashboard    │  │ Review Queue  │     │
│  │ (URL/Brand)  │  │ (Stats/Viz)  │  │ (Responses)   │     │
│  └──────────────┘  └──────────────┘  └───────────────┘     │
└─────────────────────────────────────────────────────────────┘
                           │
                    REST API (FastAPI)
                           │
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Python)                          │
│  ┌──────────────────────────────────────────────────┐       │
│  │              Scraper Module                       │       │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────────┐   │       │
│  │  │ Google   │ │ Dcard    │ │ PTT/Threads   │   │       │
│  │  │ Search   │ │ Scraper  │ │ IG Scraper    │   │       │
│  │  └──────────┘ └──────────┘ └────────────────┘   │       │
│  └──────────────────────────────────────────────────┘       │
│                                                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │              NLP Module                          │       │
│  │  ┌──────────────────┐  ┌─────────────────┐      │       │
│  │  │ Sentiment        │  │ Classification  │      │       │
│  │  │ Analysis         │  │ (Category)      │      │       │
│  │  └──────────────────┘  └─────────────────┘      │       │
│  └──────────────────────────────────────────────────┘       │
│                                                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │      Response Generation & Prioritization        │       │
│  │  ┌──────────────────────────────────────┐        │       │
│  │  │ Priority Scoring + Template Selection │        │       │
│  │  └──────────────────────────────────────┘        │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                           │
                      PostgreSQL
```

## Data Flow

1. **Input**: User provides URL or brand name
2. **Scraping**: Multi-platform scrapers extract reviews
3. **Analysis**: 
   - Sentiment analysis (positive/negative/neutral/suggestion)
   - Problem classification (logistics/quality/features/price/service)
4. **Prioritization**: Score each review by urgency
5. **Response Generation**: Create response templates
6. **Output**: Queued for user review/publication

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js, React, Tailwind CSS |
| Backend | FastAPI, Python |
| NLP | Hugging Face Transformers, PyTorch |
| Database | PostgreSQL |
| Scraping | Selenium, Playwright, BeautifulSoup |
| Async | asyncio, aiohttp |
| Deployment | Docker, Docker Compose |

## Module Responsibilities

### Scrapers
- Extract reviews from target platforms
- Handle authentication (if needed)
- Normalize data format
- Rate limiting & error handling

### NLP
- Sentiment detection (Chinese text)
- Problem classification
- Keyword extraction
- Confidence scoring

### API
- REST endpoints for frontend
- Data validation
- Response aggregation
- Async task handling

### Database
- Persistent storage
- Indexes for performance
- Audit trail
- Template management

## Security Considerations

- API authentication (TODO)
- Rate limiting on scrapers
- Sensitive data handling
- Database encryption (TODO)
- Input validation & sanitization
