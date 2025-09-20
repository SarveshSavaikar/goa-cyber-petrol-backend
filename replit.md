# Overview

Goa Cyber Patrol is a FastAPI-based backend system designed to detect online scams, fake hotels, and suspicious content from social media platforms like Telegram and Instagram. The system acts as a cyber security monitoring tool for identifying fraudulent activities targeting tourists and locals in Goa, with automated content ingestion, keyword-based flagging, and evidence logging capabilities.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Framework
- **FastAPI**: Async REST API framework serving as the main backend
- **SQLAlchemy ORM**: Database abstraction layer with declarative models
- **SQLite**: Lightweight file-based database for storing flagged posts and hotel data
- **Pydantic**: Request/response validation and serialization

## Database Design
The system uses two primary tables:
- **FlaggedPost**: Stores suspicious content with platform, message text, risk scores, and takedown recommendations
- **FakeHotel**: Tracks hotel verification status with claimed names, domains, and verification notes

## Content Ingestion Architecture
- **Telegram Integration**: Uses Telethon client for async channel message scraping
- **Instagram Integration**: Custom scraper using requests and BeautifulSoup for hashtag-based content collection
- **Async Processing**: All ingestion endpoints support concurrent data fetching from multiple sources

## Risk Assessment System
- **Keyword-based Detection**: Hardcoded suspicious keyword matching with configurable risk scoring
- **Risk Scoring Algorithm**: 0-100 scale based on keyword frequency and severity
- **Automated Categorization**: Content classified into scam types (fraud, gambling, prostitution, fake hotels)
- **Takedown Recommendations**: Predefined action suggestions mapped to content categories

## API Structure
Modular route organization:
- **Ingestion Routes**: `/ingest/*` - Data collection from social platforms
- **Flagging Routes**: `/flag/*` - Real-time content analysis
- **Dashboard Routes**: `/dashboard/*` - Statistics and analytics
- **Evidence Routes**: `/evidence/*` - Filtered log retrieval
- **Hotel Routes**: `/hotels/*` - Hotel verification management

## Security and CORS
- **CORS Middleware**: Configured for React frontend integration with wildcard origins
- **Database Session Management**: Proper connection pooling and cleanup
- **Input Validation**: Pydantic models for request validation

# External Dependencies

## Social Media APIs
- **Telegram API**: Requires API_ID and API_HASH environment variables for Telethon client authentication
- **Instagram**: Web scraping approach using public hashtag pages (no official API integration)

## Data Processing Libraries
- **Pandas**: CSV file processing for hotel verification data
- **BeautifulSoup**: HTML parsing for Instagram content extraction
- **Regex**: Pattern matching for keyword detection

## Database
- **SQLite**: Local file-based storage at `./data/flagged_posts.db`
- **No external database dependencies**: Self-contained data persistence

## Development Tools
- **Uvicorn**: ASGI server for FastAPI application
- **Python Environment**: Requires Python 3.7+ with async/await support

## Optional Integrations
- **APScheduler**: Mentioned for potential periodic scraping automation
- **Puppeteer/Playwright**: Suggested for screenshot capture functionality (not implemented)
- **Instaloader**: Alternative Instagram scraping library option