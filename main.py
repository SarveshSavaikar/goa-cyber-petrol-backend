from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Import database setup
from db import create_tables

# Import all route handlers
from routes import ingestion, flags, dashboard, evidence, hotels, alerts, settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables asynchronously
    await create_tables()
    print("PostgreSQL database tables created successfully")
    
    yield
    
    # Shutdown: Clean up if needed
    print("Application shutting down")

# Initialize FastAPI app
app = FastAPI(
    title="Goa Cyber Patrol API",
    description="FastAPI backend for detecting online scams, fake hotels, and suspicious content from Telegram and Instagram",
    version="1.0.0",
    lifespan=lifespan
)
origins = [
    "http://localhost:8080",  # Your React app's address
    "http://localhost:8000",
]

# CORS middleware for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all route handlers
app.include_router(ingestion.router)
app.include_router(flags.router)
app.include_router(dashboard.router)
app.include_router(evidence.router)
app.include_router(hotels.router)
app.include_router(alerts.router)
app.include_router(settings.router)

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Goa Cyber Patrol API",
        "description": "Backend system for detecting online scams and fake hotels",
        "version": "1.0.0",
        "endpoints": {
            "data_ingestion": [
                "POST /ingest/telegram - Fetch and analyze Telegram messages",
                "POST /ingest/instagram - Fetch and analyze Instagram posts"
            ],
            "content_analysis": [
                "POST /flag/message - Analyze message for suspicious content",
                "POST /flag/hotel - Verify hotel legitimacy"
            ],
            "dashboard": [
                "GET /dashboard/stats - Get overall statistics",
                "GET /dashboard/feed - Get live alerts feed"
            ],
            "evidence": [
                "GET /evidence - Get filtered evidence logs",
                "GET /evidence/{id} - Get detailed evidence record"
            ],
            "hotels": [
                "GET /hotels - List all checked hotels",
                "POST /hotels/check - Check hotel legitimacy",
                "POST /hotels/upload-resorts - Upload official resort database"
            ]
        },
        "features": [
            "Telegram data ingestion via Telethon",
            "Instagram hashtag scraping",
            "Rule-based keyword detection",
            "Fake hotel verification",
            "Risk scoring (0-100 scale)",
            "Automated takedown recommendations",
            "Real-time dashboard statistics",
            "Evidence logging and management"
        ]
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "message": "Goa Cyber Patrol API is running",
        "timestamp": "2024-01-01T00:00:00Z"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=5000, 
        reload=True,
        log_level="info"
    )