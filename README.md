# Brand Reputation Monitor 🧭

AI-powered brand reputation monitoring system that automatically scrapes, analyzes, and responds to customer reviews across multiple platforms.

## Features

- **Multi-platform Scraping**: Google Search, Dcard, PTT, Threads, Instagram
- **Sentiment Analysis**: AI-powered emotion detection (positive/negative/suggestion)
- **Auto-Classification**: Categorize issues (logistics/quality/features/price/service)
- **Smart Prioritization**: High-priority negative reviews first
- **Response Templates**: Automatically generate professional responses

## Tech Stack

- **Frontend**: Next.js + React
- **Backend**: Python FastAPI
- **NLP**: Hugging Face Transformers (Traditional Chinese)
- **Database**: PostgreSQL
- **Scrapers**: Selenium, Playwright, BeautifulSoup

## Project Structure

```
brand-reputation-monitor/
├── backend/          # Python backend + scrapers
├── frontend/         # Next.js frontend
├── database/         # DB schema + migrations
├── docs/             # Documentation
└── docker-compose.yml
```

## Quick Start

_(Coming soon)_

## Development

See [SETUP.md](docs/SETUP.md) for detailed setup instructions.

## Architecture

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design overview.

## License

MIT
