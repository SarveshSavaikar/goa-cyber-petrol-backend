from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from db import get_db
from models import FlaggedPost

router = APIRouter(prefix="/alerts", tags=["alerts"])

class AlertSubscription(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    platforms: List[str] = []
    min_risk_score: int = 70
    keywords: List[str] = []

@router.get("/recent")
async def get_recent_alerts(
    hours: int = Query(24, description="Number of hours to look back for alerts"),
    min_risk_score: int = Query(70, description="Minimum risk score for alerts"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: int = Query(50, description="Maximum number of alerts to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent high-risk alerts from the last N hours
    """
    try:
        # Calculate time threshold
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        # Build query
        from sqlalchemy import select
        query = select(FlaggedPost).where(
            FlaggedPost.date >= time_threshold,
            FlaggedPost.risk_score >= min_risk_score
        )
        
        if platform:
            query = query.where(FlaggedPost.platform == platform)
        
        query = query.order_by(desc(FlaggedPost.date)).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        # Format alerts for response
        alert_data = []
        for alert in alerts:
            alert_data.append({
                "id": alert.id,
                "platform": alert.platform,
                "message_snippet": alert.message_text[:200] + "..." if len(alert.message_text) > 200 else alert.message_text,
                "date": alert.date.isoformat(),
                "risk_score": alert.risk_score,
                "flagged_reason": alert.flagged_reason,
                "takedown_recommendation": alert.takedown_recommendation,
                "author_id": alert.author_id[:15] + "..." if alert.author_id and len(alert.author_id) > 15 else alert.author_id,
                "urgency": "CRITICAL" if alert.risk_score >= 90 else "HIGH" if alert.risk_score >= 80 else "MEDIUM",
                "time_ago": _calculate_time_ago(alert.date)
            })
        
        # Get alert statistics
        stats_query = select(func.count(FlaggedPost.id)).where(
            FlaggedPost.date >= time_threshold,
            FlaggedPost.risk_score >= min_risk_score
        )
        
        if platform:
            stats_query = stats_query.where(FlaggedPost.platform == platform)
        
        result = await db.execute(stats_query)
        total_alerts = result.scalar()
        
        return {
            "status": "success",
            "data": {
                "alerts": alert_data,
                "summary": {
                    "total_alerts": total_alerts,
                    "time_period_hours": hours,
                    "min_risk_score": min_risk_score,
                    "platform_filter": platform,
                    "critical_alerts": len([a for a in alert_data if a["urgency"] == "CRITICAL"]),
                    "high_alerts": len([a for a in alert_data if a["urgency"] == "HIGH"])
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent alerts: {str(e)}")

@router.post("/subscribe")
async def subscribe_to_alerts(subscription: AlertSubscription):
    """
    Subscribe to alert notifications (placeholder for future implementation)
    """
    try:
        # In a real implementation, this would:
        # 1. Save subscription to database
        # 2. Set up email/SMS notifications
        # 3. Configure alert filtering based on preferences
        
        # For MVP, we'll just validate and return success
        if not subscription.email and not subscription.phone:
            raise HTTPException(
                status_code=400, 
                detail="Either email or phone number is required for subscriptions"
            )
        
        if subscription.min_risk_score < 0 or subscription.min_risk_score > 100:
            raise HTTPException(
                status_code=400,
                detail="Risk score must be between 0 and 100"
            )
        
        return {
            "status": "success",
            "message": "Alert subscription created successfully",
            "data": {
                "subscription_id": f"sub_{hash(str(subscription.dict()))}",
                "email": subscription.email,
                "phone": subscription.phone[:5] + "***" if subscription.phone else None,
                "platforms": subscription.platforms,
                "min_risk_score": subscription.min_risk_score,
                "keywords": subscription.keywords,
                "created_at": datetime.utcnow().isoformat(),
                "status": "active",
                "note": "This is an MVP implementation - actual notifications will be implemented in production"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating alert subscription: {str(e)}")

@router.get("/statistics")
async def get_alert_statistics(
    days: int = Query(7, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get alert statistics and trends
    """
    try:
        time_threshold = datetime.utcnow() - timedelta(days=days)
        
        # Total alerts by risk level
        from sqlalchemy import select, case
        
        risk_case = case(
            (FlaggedPost.risk_score >= 90, 'critical'),
            (FlaggedPost.risk_score >= 70, 'high'),
            (FlaggedPost.risk_score >= 40, 'medium'),
            else_='low'
        )
        
        risk_level_query = select(
            risk_case.label('risk_level'),
            func.count(FlaggedPost.id).label('count')
        ).where(
            FlaggedPost.date >= time_threshold
        ).group_by(risk_case)
        
        result = await db.execute(risk_level_query)
        risk_distribution = {row.risk_level: row.count for row in result}
        
        # Platform breakdown
        platform_query = select(
            FlaggedPost.platform,
            func.count(FlaggedPost.id).label('count'),
            func.avg(FlaggedPost.risk_score).label('avg_risk')
        ).where(
            FlaggedPost.date >= time_threshold
        ).group_by(FlaggedPost.platform)
        
        result = await db.execute(platform_query)
        platform_stats = {}
        for row in result:
            platform_stats[row.platform] = {
                "count": row.count,
                "average_risk": round(float(row.avg_risk), 2)
            }
        
        # Daily trends (last 7 days)
        from sqlalchemy import cast, Date
        
        date_expr = cast(FlaggedPost.date, Date)
        daily_query = select(
            date_expr.label('date'),
            func.count(FlaggedPost.id).label('count')
        ).where(
            FlaggedPost.date >= time_threshold
        ).group_by(date_expr).order_by(date_expr)
        
        result = await db.execute(daily_query)
        daily_trends = [
            {
                "date": row.date.isoformat(),
                "count": row.count
            }
            for row in result
        ]
        
        return {
            "status": "success",
            "data": {
                "time_period_days": days,
                "risk_distribution": risk_distribution,
                "platform_breakdown": platform_stats,
                "daily_trends": daily_trends,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating alert statistics: {str(e)}")

def _calculate_time_ago(alert_date: datetime) -> str:
    """Calculate human-readable time difference"""
    now = datetime.utcnow()
    diff = now - alert_date
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"