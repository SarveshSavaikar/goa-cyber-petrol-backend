from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import Optional, List
from datetime import datetime

from db import get_db
from models import FlaggedPost

router = APIRouter(prefix="/evidence", tags=["evidence"])

@router.get("/")
async def get_evidence_logs(
    platform: Optional[str] = Query(None, description="Filter by platform (Telegram/Instagram)"),
    category: Optional[str] = Query(None, description="Filter by flagged reason category"),
    min_risk_score: Optional[int] = Query(0, description="Minimum risk score filter"),
    limit: int = Query(50, description="Number of records to return"),
    offset: int = Query(0, description="Number of records to skip"),
    db: Session = Depends(get_db)
):
    """
    Get filterable evidence logs with platform/category/risk filters
    """
    try:
        query = db.query(FlaggedPost)
        
        # Apply filters
        if platform:
            query = query.filter(FlaggedPost.platform == platform)
        
        if category:
            query = query.filter(FlaggedPost.flagged_reason.like(f"%{category}%"))
        
        if min_risk_score > 0:
            query = query.filter(FlaggedPost.risk_score >= min_risk_score)
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination and ordering
        evidence_logs = query.order_by(desc(FlaggedPost.date)).offset(offset).limit(limit).all()
        
        logs_data = []
        for log in evidence_logs:
            logs_data.append({
                "id": log.id,
                "platform": log.platform,
                "message_snippet": log.message_text[:200] + "..." if len(log.message_text) > 200 else log.message_text,
                "date": log.date.isoformat(),
                "flagged_reason": log.flagged_reason,
                "risk_score": log.risk_score,
                "author_id": log.author_id[:15] + "..." if log.author_id and len(log.author_id) > 15 else log.author_id,
                "takedown_recommendation": log.takedown_recommendation,
                "screenshot_available": bool(log.screenshot_path),
                "risk_level": "HIGH" if log.risk_score >= 70 else "MEDIUM" if log.risk_score >= 40 else "LOW"
            })
        
        return {
            "status": "success",
            "data": {
                "evidence_logs": logs_data,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total_count
                },
                "filters_applied": {
                    "platform": platform,
                    "category": category,
                    "min_risk_score": min_risk_score
                }
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching evidence logs: {str(e)}")

@router.get("/{evidence_id}")
async def get_evidence_detail(evidence_id: int, db: Session = Depends(get_db)):
    """
    Get full details of a specific evidence record including highlighted keywords
    """
    try:
        evidence = db.query(FlaggedPost).filter(FlaggedPost.id == evidence_id).first()
        
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence record not found")
        
        # Extract keywords that were flagged
        from utils.keyword_checker import SCAM_KEYWORDS
        highlighted_keywords = []
        message_lower = evidence.message_text.lower()
        
        for keyword in SCAM_KEYWORDS:
            if keyword.lower() in message_lower:
                highlighted_keywords.append(keyword)
        
        return {
            "status": "success",
            "data": {
                "id": evidence.id,
                "platform": evidence.platform,
                "full_message": evidence.message_text,
                "date": evidence.date.isoformat(),
                "flagged_reason": evidence.flagged_reason,
                "risk_score": evidence.risk_score,
                "author_id": evidence.author_id,
                "takedown_recommendation": evidence.takedown_recommendation,
                "screenshot_path": evidence.screenshot_path,
                "highlighted_keywords": highlighted_keywords,
                "analysis": {
                    "word_count": len(evidence.message_text.split()),
                    "character_count": len(evidence.message_text),
                    "risk_level": "HIGH" if evidence.risk_score >= 70 else "MEDIUM" if evidence.risk_score >= 40 else "LOW",
                    "urgency": "IMMEDIATE" if evidence.risk_score >= 85 else "NORMAL"
                }
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching evidence detail: {str(e)}")

@router.get("/stats/summary")
async def get_evidence_summary(db: Session = Depends(get_db)):
    """
    Get summary statistics for evidence logs
    """
    try:
        from sqlalchemy import func
        
        # Total evidence count
        total_evidence = db.query(FlaggedPost).count()
        
        # Platform distribution
        platform_stats = db.query(
            FlaggedPost.platform,
            func.count(FlaggedPost.id).label('count'),
            func.avg(FlaggedPost.risk_score).label('avg_risk')
        ).group_by(FlaggedPost.platform).all()
        
        platform_summary = {}
        for platform, count, avg_risk in platform_stats:
            platform_summary[platform] = {
                "count": count,
                "average_risk_score": round(float(avg_risk) if avg_risk else 0, 2)
            }
        
        # Risk level distribution
        high_risk_count = db.query(FlaggedPost).filter(FlaggedPost.risk_score >= 70).count()
        medium_risk_count = db.query(FlaggedPost).filter(
            FlaggedPost.risk_score >= 40,
            FlaggedPost.risk_score < 70
        ).count()
        low_risk_count = db.query(FlaggedPost).filter(FlaggedPost.risk_score < 40).count()
        
        # Recent trends (last 7 days)
        from datetime import timedelta
        last_week = datetime.utcnow() - timedelta(days=7)
        recent_evidence = db.query(FlaggedPost).filter(FlaggedPost.date >= last_week).count()
        
        return {
            "status": "success",
            "data": {
                "summary": {
                    "total_evidence_records": total_evidence,
                    "recent_evidence_7_days": recent_evidence,
                    "platform_breakdown": platform_summary,
                    "risk_distribution": {
                        "high_risk": high_risk_count,
                        "medium_risk": medium_risk_count,
                        "low_risk": low_risk_count
                    }
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating evidence summary: {str(e)}")