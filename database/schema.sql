-- Brand Reputation Monitor Database Schema

-- Reviews table
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,  -- 'google', 'dcard', 'ptt', 'threads', 'instagram'
    brand_id INTEGER NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    author VARCHAR(255),
    rating FLOAT,
    url VARCHAR(2000),
    sentiment VARCHAR(50),  -- 'positive', 'negative', 'neutral', 'suggestion'
    sentiment_score FLOAT,
    category VARCHAR(50),  -- 'logistics', 'quality', 'features', 'price', 'service', 'other'
    priority INTEGER,  -- 1 (high) to 5 (low)
    posted_at TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_brand FOREIGN KEY (brand_id) REFERENCES brands(id)
);

-- Brands table
CREATE TABLE brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Response templates table
CREATE TABLE response_templates (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER NOT NULL,
    category VARCHAR(50),  -- Problem category this template applies to
    sentiment VARCHAR(50),  -- What sentiment this addresses
    template_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_brand FOREIGN KEY (brand_id) REFERENCES brands(id)
);

-- Review responses (generated responses)
CREATE TABLE review_responses (
    id SERIAL PRIMARY KEY,
    review_id INTEGER NOT NULL,
    response_text TEXT NOT NULL,
    status VARCHAR(50),  -- 'draft', 'approved', 'published'
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_review FOREIGN KEY (review_id) REFERENCES reviews(id)
);

-- Create indexes for better query performance
CREATE INDEX idx_reviews_brand_id ON reviews(brand_id);
CREATE INDEX idx_reviews_sentiment ON reviews(sentiment);
CREATE INDEX idx_reviews_category ON reviews(category);
CREATE INDEX idx_reviews_priority ON reviews(priority);
CREATE INDEX idx_reviews_source ON reviews(source);
CREATE INDEX idx_response_templates_brand_id ON response_templates(brand_id);
CREATE INDEX idx_review_responses_review_id ON review_responses(review_id);
