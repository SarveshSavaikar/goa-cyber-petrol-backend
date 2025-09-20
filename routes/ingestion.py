from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Optional
import asyncio
from pydantic import BaseModel

from db import get_db
from models import FlaggedPost
from utils.telegram_client import telegram_scraper
from utils.instagram_scraper import instagram_scraper
from utils.website_scraper import website_scraper
from utils.keyword_checker import check_keywords

router = APIRouter(prefix="/ingest", tags=["ingestion"])

class IngestionRequest(BaseModel):
    channels: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None
    urls: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    limit: int = 50

@router.post("/telegram")
async def ingest_telegram_data(
    request: IngestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch latest Telegram messages and save flagged posts to database
    """
    try:
        channels = request.channels or ["goatourism", "goajobs", "goabusiness"]
        
        # Fetch messages from Telegram
        messages = await telegram_scraper.get_messages_from_channels(channels, request.limit)
        
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
        
        await db.commit()
        
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
    request: IngestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch latest Instagram posts by hashtags and save flagged posts to database
    """
    try:
        hashtags = request.hashtags or ["goa", "goahotel", "goajobs", "easymoney", "workfromhome"]
        
        # Fetch posts from Instagram
        posts = instagram_scraper.scrape_hashtag_posts(hashtags, request.limit // len(hashtags) if hashtags else 20)
        
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
        
        await db.commit()
        
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

@router.post("/website")
async def ingest_website_data(
    request: IngestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Scrape and analyze website content for suspicious activity
    """
    try:
        urls = request.urls or ["https://www.goatourism.gov.in/"]
        
        # Scrape websites
        website_content = await website_scraper.scrape_website_content(urls)
        
        flagged_count = 0
        flagged_posts = []
        
        for content in website_content:
            if content.get('status') == 'success':
                # Check content for suspicious activity
                risk_score, flagged_reason, takedown_recommendation = check_keywords(content['message_text'])
                
                if risk_score > 0:
                    flagged_post = FlaggedPost(
                        platform="Website",
                        message_text=content['message_text'],
                        date=content['date'],
                        flagged_reason=flagged_reason,
                        risk_score=risk_score,
                        author_id=content['domain'],
                        takedown_recommendation=takedown_recommendation
                    )
                    
                    db.add(flagged_post)
                    flagged_count += 1
                    
                    flagged_posts.append({
                        "url": content['url'],
                        "domain": content['domain'],
                        "risk_score": risk_score,
                        "flagged_reason": flagged_reason
                    })
        
        await db.commit()
        
        return {
            "status": "success",
            "message": f"Processed {len(website_content)} websites",
            "data": {
                "total_websites": len(website_content),
                "flagged_posts": flagged_count,
                "urls_monitored": urls,
                "sample_flagged": flagged_posts[:5]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting website data: {str(e)}")

@router.post("/social")
async def ingest_social_media_data(
    request: IngestionRequest,
    platform: str = "facebook",
    db: AsyncSession = Depends(get_db)
):
    """
    Scrape social media posts for analysis
    """
    try:
        keywords = request.keywords or ["goa", "scam", "fraud"]
        hashtags = request.hashtags or ["goa", "tourism"]
        
        # Scrape social media content
        posts = website_scraper.scrape_social_media_posts(platform, hashtags, keywords)
        
        flagged_count = 0
        flagged_posts = []
        
        for post in posts:
            if post.get('status') != 'error':
                # Check post for suspicious activity
                risk_score, flagged_reason, takedown_recommendation = check_keywords(post['message_text'])
                
                if risk_score > 0:
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
                        "platform": post['platform'],
                        "message_snippet": post['message_text'][:100] + "...",
                        "risk_score": risk_score,
                        "flagged_reason": flagged_reason
                    })
        
        await db.commit()
        
        return {
            "status": "success",
            "message": f"Processed {len(posts)} {platform} posts",
            "data": {
                "total_posts": len(posts),
                "flagged_posts": flagged_count,
                "platform": platform,
                "keywords_used": keywords,
                "hashtags_used": hashtags,
                "sample_flagged": flagged_posts[:5]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting social media data: {str(e)}")