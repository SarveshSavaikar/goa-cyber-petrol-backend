from fastapi import APIRouter, Depends , Query
from sqlalchemy.orm import Session , sessionmaker, joinedload
from sqlalchemy import func, desc
from typing import List, Dict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, select  
from models import * 

from db import get_db
from models import FlaggedPost, FakeHotel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Get overall statistics for the dashboard (Async Version)
    """
    try:
        # Total posts scanned
        total_posts = (await db.execute(select(func.count(FlaggedPost.id)))).scalar()
        print("Total Posts are  :- ", total_posts)
        
        # Suspicious content count (risk >= 40)
        suspicious_posts = (await db.execute(
            select(func.count(FlaggedPost.id)).where(FlaggedPost.risk_score >= 40)
        )).scalar()

        # High-risk alerts (risk >= 70)
        high_risk_alerts = (await db.execute(
            select(func.count(FlaggedPost.id)).where(FlaggedPost.risk_score >= 70)
        )).scalar()

        # Fake hotels detected
        fake_hotels = (await db.execute(
            select(func.count(FakeHotel.id)).where(FakeHotel.status.like("%❌%"))
        )).scalar()

        # Platform breakdown
        # Corrected: group by platform_id
        platform_stats = (await db.execute(
            select(FlaggedPost.platform_id, func.count(FlaggedPost.id)).group_by(FlaggedPost.platform_id)
        )).all()
        
        platform_data = {platform_id: count for platform_id, count in platform_stats}

        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_posts = (await db.execute(
            select(func.count(FlaggedPost.id)).where(FlaggedPost.date >= yesterday)
        )).scalar()

        # Risk distribution
        low_risk = (await db.execute(
            select(func.count(FlaggedPost.id)).where(FlaggedPost.risk_score < 40)
        )).scalar()

        medium_risk = (await db.execute(
            select(func.count(FlaggedPost.id)).where(
                FlaggedPost.risk_score >= 40,
                FlaggedPost.risk_score < 70
            )
        )).scalar()

        high_risk = (await db.execute(
            select(func.count(FlaggedPost.id)).where(FlaggedPost.risk_score >= 70)
        )).scalar()

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
        # Return a more specific error message in a development environment
        print(f"Error: {e}") 
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
        
@router.get("/category_breakdown")
async def get_category_breakdown(db: AsyncSession = Depends(get_db)):
    """
    Get data for the category breakdown chart.
    This endpoint uses the 'flagged_reason' and 'fake_hotels' data from the database.
    """
    try:
        # Counts for flagged posts by category
        loan_scams_result = await db.execute(
            select(func.count(FlaggedPost.id)).where(FlaggedPost.flagged_reason == "Loan Scam")
        )
        loan_scams = loan_scams_result.scalar_one_or_none() or 0

        fake_jobs_result = await db.execute(
            select(func.count(FlaggedPost.id)).where(FlaggedPost.flagged_reason == "Job Scam")
        )
        fake_jobs = fake_jobs_result.scalar_one_or_none() or 0
        
        # Prostitution and gambling are grouped together.
        prostitution_gambling_result = await db.execute(
            select(func.count(FlaggedPost.id)).where(
                FlaggedPost.flagged_reason.in_(["Prostitution", "Gambling"])
            )
        )
        prostitution_gambling = prostitution_gambling_result.scalar_one_or_none() or 0

        # Count fake hotels with a '❌' status.
        fake_hotels_result = await db.execute(
            select(func.count(FakeHotel.id)).where(FakeHotel.status.like("%❌%"))
        )
        fake_hotels = fake_hotels_result.scalar_one_or_none() or 0

        return [
            {
                "name": "Loan Scams",
                "value": loan_scams,
                "color": "#0072b2"  # Blue color
            },
            {
                "name": "Fake Jobs",
                "value": fake_jobs,
                "color": "#009e73"  # Green color
            },
            {
                "name": "Prostitution / Gambling",
                "value": prostitution_gambling,
                "color": "#e69f00"  # Orange color
            },
            {
                "name": "Fake Hotels",
                "value": fake_hotels,
                "color": "#d55e00"  # Red color
            }
        ]
        
    except Exception as e:
        print(f"Error: {e}")
        return [
            {"name": "Loan Scams", "value": 0, "color": "#0072b2"},
            {"name": "Fake Jobs", "value": 0, "color": "#009e73"},
            {"name": "Prostitution / Gambling", "value": 0, "color": "#e69f00"},
            {"name": "Fake Hotels", "value": 0, "color": "#d55e00"}
        ]

# Endpoint for category breakdown.
@router.get("/dashboard/category_breakdown")
async def get_category_breakdown(db: AsyncSession = Depends(get_db)):
    """
    Get data for the category breakdown chart.
    This endpoint uses the 'flagged_reason' and 'fake_hotels' data from the database.
    """
    try:
        # Count posts by flagged reason
        category_counts_result = await db.execute(
            select(
                FlaggedPost.flagged_reason,
                func.count(FlaggedPost.id)
            ).group_by(FlaggedPost.flagged_reason)
        )
        category_counts = category_counts_result.all()

        category_dict = {reason: count for reason, count in category_counts}

        # Count fake hotels with a '❌' status.
        fake_hotels_result = await db.execute(
            select(func.count(FakeHotel.id)).where(FakeHotel.status.like("%❌%"))
        )
        fake_hotels = fake_hotels_result.scalar_one_or_none() or 0

        return [
            {
                "category": "Loan Scams",
                "value": category_dict.get("Loan Scam", 0),
                "color": "#0072b2"  # Blue color
            },
            {
                "category": "Fake Jobs",
                "value": category_dict.get("Job Scam", 0),
                "color": "#009e73"  # Green color
            },
            {
                "category": "Prostitution / Gambling",
                "value": category_dict.get("Prostitution", 0) + category_dict.get("Gambling", 0),
                "color": "#e69f00"  # Orange color
            },
            {
                "category": "Fake Hotels",
                "value": fake_hotels,
                "color": "#d55e00"  # Red color
            }
        ]
        
    except Exception as e:
        print(f"Error: {e}")
        return [
            {"category": "Loan Scams", "value": 0, "color": "#0072b2"},
            {"category": "Fake Jobs", "value": 0, "color": "#009e73"},
            {"category": "Prostitution / Gambling", "value": 0, "color": "#e69f00"},
            {"category": "Fake Hotels", "value": 0, "color": "#d55e00"}
        ]

# The new endpoint for live feed.
@router.get("/feed")
async def get_live_feed(
    limit: int = Query(20, ge=1),
    platform: str = Query(None),
    min_risk_score: int = Query(0, ge=0, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get latest flagged posts for live alerts feed with filtering.
    """
    try:
        # Start with a base query and eagerly load relationships
        query = select(FlaggedPost).options(joinedload(FlaggedPost.platform_rel), joinedload(FlaggedPost.user_rel))
        
        # Filter by platform name if specified
        if platform:
            query = query.where(Platform.name.ilike(f"%{platform}%"))
        
        # Filter by minimum risk score
        if min_risk_score > 0:
            query = query.where(FlaggedPost.risk_score >= min_risk_score)
        
        # Order by date in descending order and apply limit
        posts_result = await db.execute(
            query.order_by(desc(FlaggedPost.date)).limit(limit)
        )
        posts = posts_result.scalars().all()
        
        feed_data = []
        for post in posts:
            # Corrected attribute access to use 'user_rel' and 'platform_rel'
            author_username = post.user_rel.username if post.user_rel else "N/A"
            message_snippet = post.message_text[:150] + "..." if post.message_text and len(post.message_text) > 150 else post.message_text
            risk_level = "HIGH" if post.risk_score >= 70 else ("MEDIUM" if post.risk_score >= 40 else "LOW")
            
            feed_data.append({
                "id": post.id,
                "platform": post.platform_rel.name if post.platform_rel else "N/A",
                "snippet": message_snippet,
                "timestamp": post.date.isoformat(),
                "category": post.flagged_reason,
                "riskLevel": risk_level
            })
        
        return feed_data
    
    except Exception as e:
        print(f"Error: {e}")
        return []
