from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict
import pandas as pd
import os

from db import get_db
from models import FakeHotel
from utils.keyword_checker import check_keywords

router = APIRouter(prefix="/flag", tags=["flagging"])

class MessageRequest(BaseModel):
    message_text: str

class HotelRequest(BaseModel):
    hotel_name: str
    website_domain: str = None

@router.post("/message")
async def flag_message(request: MessageRequest):
    """
    Analyze message text for suspicious content and return risk score
    """
    try:
        risk_score, flagged_reason, takedown_recommendation = check_keywords(request.message_text)
        
        return {
            "status": "success",
            "data": {
                "message_text": request.message_text[:200] + "..." if len(request.message_text) > 200 else request.message_text,
                "risk_score": risk_score,
                "flagged_reason": flagged_reason,
                "takedown_recommendation": takedown_recommendation,
                "is_high_risk": risk_score >= 70,
                "analysis": {
                    "low_risk": risk_score < 40,
                    "medium_risk": 40 <= risk_score < 70,
                    "high_risk": risk_score >= 70
                }
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing message: {str(e)}")

@router.post("/hotel")
async def flag_hotel(request: HotelRequest, db: Session = Depends(get_db)):
    """
    Check if hotel is legitimate by comparing against official resort list
    """
    try:
        # Load official resorts CSV
        csv_path = "data/official_resorts.csv"
        
        if not os.path.exists(csv_path):
            # Return a warning if CSV doesn't exist
            status = "❌ Fake"
            notes = "Cannot verify - Official resort database not found"
        else:
            # Load and check against official list
            df = pd.read_csv(csv_path)
            
            # Check if hotel name matches any official resort
            hotel_matches = df[df['name'].str.contains(request.hotel_name, case=False, na=False)]
            
            if not hotel_matches.empty:
                status = "✅ Official"
                notes = f"Verified official resort: {hotel_matches.iloc[0]['name']}"
            else:
                # Check for partial matches or similar names
                partial_matches = df[df['name'].str.contains(
                    request.hotel_name.split()[0], case=False, na=False
                )] if request.hotel_name.split() else []
                
                if not partial_matches.empty:
                    status = "⚠️ Uncertain"
                    notes = f"Similar official resort found: {partial_matches.iloc[0]['name']}. Requires manual verification."
                else:
                    status = "❌ Fake"
                    notes = "Not found in official resort database - potentially fake"
        
        # Save to database
        fake_hotel = FakeHotel(
            claimed_name=request.hotel_name,
            website_domain=request.website_domain,
            status=status,
            notes=notes
        )
        
        db.add(fake_hotel)
        db.commit()
        
        # Determine takedown recommendation
        if status == "❌ Fake":
            takedown_recommendation = "Report to Tourism Dept"
        elif status == "⚠️ Uncertain":
            takedown_recommendation = "Manual investigation required"
        else:
            takedown_recommendation = "No action needed - verified official"
        
        return {
            "status": "success",
            "data": {
                "hotel_name": request.hotel_name,
                "website_domain": request.website_domain,
                "verification_status": status,
                "notes": notes,
                "takedown_recommendation": takedown_recommendation,
                "is_suspicious": status in ["❌ Fake", "⚠️ Uncertain"]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking hotel: {str(e)}")