# Setup Instructions

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Git

## Backend Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Download NLP Models

```bash
python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; AutoTokenizer.from_pretrained('bert-base-chinese'); AutoModelForSequenceClassification.from_pretrained('bert-base-chinese')"
```

### 4. Setup Environment Variables

Create `.env` file:

```
DATABASE_URL=postgresql://user:password@localhost/brand_monitor
GOOGLE_API_KEY=your_key_here
API_HOST=0.0.0.0
API_PORT=8000
```

### 5. Initialize Database

```bash
psql -U postgres -c "CREATE DATABASE brand_monitor;"
psql -U postgres -d brand_monitor -f ../database/schema.sql
```

### 6. Run API Server

```bash
cd backend
python -m api.main
```

Server will be available at `http://localhost:8000`

API docs: `http://localhost:8000/docs`

## Frontend Setup

### 1. Create Next.js Project

```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Environment Variables

Create `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Run Development Server

```bash
npm run dev
```

Frontend available at `http://localhost:3000`

## Docker Setup (Alternative)

### 1. Build Images

```bash
docker-compose build
```

### 2. Start Services

```bash
docker-compose up
```

Services:
- API: http://localhost:8000
- Frontend: http://localhost:3000
- Database: localhost:5432

## Development Workflow

1. **Backend Development**
   ```bash
   cd backend
   source venv/bin/activate
   python -m api.main
   ```

2. **Frontend Development**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Database Changes**
   - Update `database/schema.sql`
   - Apply with: `psql -d brand_monitor -f database/schema.sql`

## Testing

### Backend Tests

```bash
pytest backend/tests/
```

### Frontend Tests

```bash
npm run test
```

## Deployment

_(Coming soon)_

## Troubleshooting

### Database Connection Issues

- Check PostgreSQL is running: `psql --version`
- Verify credentials in `.env`
- Check DATABASE_URL format

### NLP Model Download Issues

- May be slow on first run (2-3GB download)
- Can pre-download: `huggingface-cli download bert-base-chinese`

### Port Conflicts

- API default: 8000
- Frontend default: 3000
- Change in environment variables if needed

## Next Steps

1. Implement scrapers for each platform
2. Fine-tune NLP models on sample reviews
3. Design frontend UI components
4. Test end-to-end workflow
