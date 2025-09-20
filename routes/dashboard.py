from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict
from datetime import datetime, timedelta

from db import get_db
from models import FlaggedPost, FakeHotel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get overall statistics for the dashboard
    """
    try:
        # Total posts scanned
        total_posts = db.query(FlaggedPost).count()
        
        # Suspicious content count
        suspicious_posts = db.query(FlaggedPost).filter(FlaggedPost.risk_score >= 40).count()
        
        # High-risk alerts (70+)
        high_risk_alerts = db.query(FlaggedPost).filter(FlaggedPost.risk_score >= 70).count()
        
        # Fake hotels detected
        fake_hotels = db.query(FakeHotel).filter(FakeHotel.status.like("%❌%")).count()
        
        # Platform breakdown
        platform_stats = db.query(
            FlaggedPost.platform,
            func.count(FlaggedPost.id).label('count')
        ).group_by(FlaggedPost.platform).all()
        
        platform_data = {platform: count for platform, count in platform_stats}
        
        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_posts = db.query(FlaggedPost).filter(FlaggedPost.date >= yesterday).count()
        
        # Risk score distribution
        low_risk = db.query(FlaggedPost).filter(FlaggedPost.risk_score < 40).count()
        medium_risk = db.query(FlaggedPost).filter(
            FlaggedPost.risk_score >= 40,
            FlaggedPost.risk_score < 70
        ).count()
        high_risk = db.query(FlaggedPost).filter(FlaggedPost.risk_score >= 70).count()
        
        return {
            "status": "success",
            "data": {
                "overview": {
                    "total_posts_scanned": total_posts,
                    "suspicious_content": suspicious_posts,
                    "high_risk_alerts": high_risk_alerts,
                    "fake_hotels_detected": fake_hotels,
                    "recent_activity_24h": recent_posts
                },
                "platform_breakdown": platform_data,
                "risk_distribution": {
                    "low_risk": low_risk,
                    "medium_risk": medium_risk,
                    "high_risk": high_risk
                },
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error fetching dashboard stats: {str(e)}",
            "data": {
                "overview": {
                    "total_posts_scanned": 0,
                    "suspicious_content": 0,
                    "high_risk_alerts": 0,
                    "fake_hotels_detected": 0,
                    "recent_activity_24h": 0
                },
                "platform_breakdown": {},
                "risk_distribution": {
                    "low_risk": 0,
                    "medium_risk": 0,
                    "high_risk": 0
                }
            }
        }

@router.get("/feed")
async def get_live_feed(
    limit: int = 20,
    platform: str = None,
    min_risk_score: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get latest flagged posts for live alerts feed
    """
    try:
        query = db.query(FlaggedPost)
        
        # Filter by platform if specified
        if platform:
            query = query.filter(FlaggedPost.platform == platform)
        
        # Filter by minimum risk score
        if min_risk_score > 0:
            query = query.filter(FlaggedPost.risk_score >= min_risk_score)
        
        # Get latest posts ordered by date
        posts = query.order_by(desc(FlaggedPost.date)).limit(limit).all()
        
        feed_data = []
        for post in posts:
            feed_data.append({
                "id": post.id,
                "platform": post.platform,
                "message_snippet": post.message_text[:150] + "..." if len(post.message_text) > 150 else post.message_text,
                "date": post.date.isoformat(),
                "risk_score": post.risk_score,
                "flagged_reason": post.flagged_reason,
                "takedown_recommendation": post.takedown_recommendation,
                "author_id": post.author_id[:10] + "..." if post.author_id and len(post.author_id) > 10 else post.author_id,
                "risk_level": "HIGH" if post.risk_score >= 70 else "MEDIUM" if post.risk_score >= 40 else "LOW"
            })
        
        return {
            "status": "success",
            "data": {
                "feed": feed_data,
                "total_count": len(feed_data),
                "filters_applied": {
                    "platform": platform,
                    "min_risk_score": min_risk_score,
                    "limit": limit
                },
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error fetching live feed: {str(e)}",
            "data": {
                "feed": [],
                "total_count": 0
            }
        }