from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
import asyncio

from db import get_db
from models import FlaggedPost
from utils.telegram_client import telegram_scraper
from utils.instagram_scraper import instagram_scraper
from utils.keyword_checker import check_keywords

router = APIRouter(prefix="/ingest", tags=["ingestion"])

@router.post("/telegram")
async def ingest_telegram_data(
    channels: List[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Fetch latest Telegram messages and save flagged posts to database
    """
    try:
        if not channels:
            # Default channels to monitor (users can modify this)
            channels = ["goatourism", "goajobs", "goabusiness"]
        
        # Fetch messages from Telegram
        messages = await telegram_scraper.get_messages_from_channels(channels, limit)
        
        flagged_count = 0
        flagged_posts = []
        
        for message in messages:
            # Check each message for suspicious content
            risk_score, flagged_reason, takedown_recommendation = check_keywords(message['message_text'])
            
            if risk_score > 0:  # Only save flagged posts
                flagged_post = FlaggedPost(
                    platform=message['platform'],
                    message_text=message['message_text'],
                    date=message['date'],
                    flagged_reason=flagged_reason,
                    risk_score=risk_score,
                    author_id=message['author_id'],
                    takedown_recommendation=takedown_recommendation
                )
                
                db.add(flagged_post)
                flagged_count += 1
                
                flagged_posts.append({
                    "message_text": message['message_text'][:100] + "...",
                    "risk_score": risk_score,
                    "flagged_reason": flagged_reason,
                    "channel": message.get('channel', 'Unknown')
                })
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Processed {len(messages)} messages from Telegram",
            "data": {
                "total_messages": len(messages),
                "flagged_posts": flagged_count,
                "channels_monitored": channels,
                "sample_flagged": flagged_posts[:5]  # Show first 5 flagged posts
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting Telegram data: {str(e)}")

@router.post("/instagram")
async def ingest_instagram_data(
    hashtags: List[str] = None,
    limit_per_hashtag: int = 20,
    db: Session = Depends(get_db)
):
    """
    Fetch latest Instagram posts by hashtags and save flagged posts to database
    """
    try:
        if not hashtags:
            # Default hashtags to monitor
            hashtags = ["goa", "goahotel", "goajobs", "easymoney", "workfromhome"]
        
        # Fetch posts from Instagram
        posts = instagram_scraper.scrape_hashtag_posts(hashtags, limit_per_hashtag)
        
        flagged_count = 0
        flagged_posts = []
        
        for post in posts:
            # Check each post for suspicious content
            risk_score, flagged_reason, takedown_recommendation = check_keywords(post['message_text'])
            
            if risk_score > 0:  # Only save flagged posts
                flagged_post = FlaggedPost(
                    platform=post['platform'],
                    message_text=post['message_text'],
                    date=post['date'],
                    flagged_reason=flagged_reason,
                    risk_score=risk_score,
                    author_id=post['author_id'],
                    takedown_recommendation=takedown_recommendation
                )
                
                db.add(flagged_post)
                flagged_count += 1
                
                flagged_posts.append({
                    "message_text": post['message_text'][:100] + "...",
                    "risk_score": risk_score,
                    "flagged_reason": flagged_reason,
                    "hashtag": post.get('hashtag', 'Unknown')
                })
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Processed {len(posts)} posts from Instagram",
            "data": {
                "total_posts": len(posts),
                "flagged_posts": flagged_count,
                "hashtags_monitored": hashtags,
                "sample_flagged": flagged_posts[:5]  # Show first 5 flagged posts
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting Instagram data: {str(e)}")