from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import os
import shutil

from db import get_db
from models import FakeHotel

router = APIRouter(prefix="/hotels", tags=["hotels"])

class HotelCheckRequest(BaseModel):
    hotel_name: str
    website_domain: Optional[str] = None

@router.get("/")
async def get_all_hotels(
    limit: int = Query(50, description="Number of hotels to return"),
    offset: int = Query(0, description="Number of hotels to skip"),
    status_filter: Optional[str] = Query(None, description="Filter by status (Official/Fake)"),
    db: Session = Depends(get_db)
):
    """
    Get list of all checked hotels with optional filtering
    """
    try:
        query = db.query(FakeHotel)
        
        # Apply status filter if specified
        if status_filter:
            if "official" in status_filter.lower():
                query = query.filter(FakeHotel.status.like("%✅%"))
            elif "fake" in status_filter.lower():
                query = query.filter(FakeHotel.status.like("%❌%"))
            elif "uncertain" in status_filter.lower():
                query = query.filter(FakeHotel.status.like("%⚠️%"))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        hotels = query.order_by(desc(FakeHotel.id)).offset(offset).limit(limit).all()
        
        hotels_data = []
        for hotel in hotels:
            hotels_data.append({
                "id": hotel.id,
                "claimed_name": hotel.claimed_name,
                "website_domain": hotel.website_domain,
                "status": hotel.status,
                "notes": hotel.notes,
                "has_screenshot": bool(hotel.screenshot),
                "is_suspicious": hotel.status in ["❌ Fake", "⚠️ Uncertain"]
            })
        
        return {
            "status": "success",
            "data": {
                "hotels": hotels_data,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total_count
                },
                "filters_applied": {
                    "status_filter": status_filter
                }
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching hotels: {str(e)}")

@router.post("/check")
async def check_hotel_legitimacy(request: HotelCheckRequest, db: Session = Depends(get_db)):
    """
    Check if a hotel is legitimate by comparing against official resort database
    """
    try:
        csv_path = "data/official_resorts.csv"
        
        if not os.path.exists(csv_path):
            status = "❌ Fake"
            notes = "Cannot verify - Official resort database not available"
            confidence = "Low"
        else:
            # Load official resorts data
            df = pd.read_csv(csv_path)
            
            # Exact name match
            exact_matches = df[df['name'].str.contains(request.hotel_name, case=False, na=False)]
            
            if not exact_matches.empty:
                status = "✅ Official"
                notes = f"Verified official resort: {exact_matches.iloc[0]['name']}"
                confidence = "High"
            else:
                # Check for partial matches
                words = request.hotel_name.split()
                partial_matches = []
                
                for word in words:
                    if len(word) > 3:  # Only check meaningful words
                        matches = df[df['name'].str.contains(word, case=False, na=False)]
                        if not matches.empty:
                            partial_matches.extend(matches.to_dict('records'))
                
                if partial_matches:
                    status = "⚠️ Uncertain"
                    similar_name = partial_matches[0]['name']
                    notes = f"Similar official resort found: {similar_name}. Manual verification recommended."
                    confidence = "Medium"
                else:
                    status = "❌ Fake"
                    notes = "Not found in official resort database - potentially fraudulent"
                    confidence = "High"
        
        # Check if this hotel was already checked
        existing_hotel = db.query(FakeHotel).filter(
            FakeHotel.claimed_name == request.hotel_name
        ).first()
        
        if existing_hotel:
            # Update existing record
            existing_hotel.status = status
            existing_hotel.notes = notes
            existing_hotel.website_domain = request.website_domain
            hotel_id = existing_hotel.id
        else:
            # Create new record
            new_hotel = FakeHotel(
                claimed_name=request.hotel_name,
                website_domain=request.website_domain,
                status=status,
                notes=notes
            )
            db.add(new_hotel)
            db.commit()
            hotel_id = new_hotel.id
        
        db.commit()
        
        # Determine recommended actions
        if status == "❌ Fake":
            recommended_action = "Report to Tourism Department immediately"
            urgency = "High"
        elif status == "⚠️ Uncertain":
            recommended_action = "Conduct manual investigation and cross-reference"
            urgency = "Medium"
        else:
            recommended_action = "No action required - legitimate business"
            urgency = "None"
        
        return {
            "status": "success",
            "data": {
                "hotel_id": hotel_id,
                "hotel_name": request.hotel_name,
                "website_domain": request.website_domain,
                "verification_status": status,
                "confidence_level": confidence,
                "notes": notes,
                "recommended_action": recommended_action,
                "urgency": urgency,
                "is_suspicious": status in ["❌ Fake", "⚠️ Uncertain"]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking hotel: {str(e)}")

@router.get("/stats")
async def get_hotel_statistics(db: Session = Depends(get_db)):
    """
    Get statistics about checked hotels
    """
    try:
        from sqlalchemy import func
        
        # Total hotels checked
        total_hotels = db.query(FakeHotel).count()
        
        # Status breakdown
        official_count = db.query(FakeHotel).filter(FakeHotel.status.like("%✅%")).count()
        fake_count = db.query(FakeHotel).filter(FakeHotel.status.like("%❌%")).count()
        uncertain_count = db.query(FakeHotel).filter(FakeHotel.status.like("%⚠️%")).count()
        
        # Recent checks (last 7 days)
        from datetime import datetime, timedelta
        last_week = datetime.utcnow() - timedelta(days=7)
        # Note: We don't have a created_at field, so we'll count all for now
        recent_checks = total_hotels  # This would be filtered by date in a real implementation
        
        return {
            "status": "success",
            "data": {
                "summary": {
                    "total_hotels_checked": total_hotels,
                    "official_verified": official_count,
                    "fake_detected": fake_count,
                    "uncertain_cases": uncertain_count,
                    "recent_checks_7_days": recent_checks
                },
                "verification_rates": {
                    "official_percentage": round((official_count / max(total_hotels, 1)) * 100, 2),
                    "fake_percentage": round((fake_count / max(total_hotels, 1)) * 100, 2),
                    "uncertain_percentage": round((uncertain_count / max(total_hotels, 1)) * 100, 2)
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating hotel statistics: {str(e)}")

@router.post("/upload-resorts")
async def upload_official_resorts(file: UploadFile = File(...)):
    """
    Upload CSV file to replace/update official resort list
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Save uploaded file
        csv_path = "data/official_resorts.csv"
        
        # Create backup of existing file if it exists
        if os.path.exists(csv_path):
            backup_path = f"data/official_resorts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            shutil.copy2(csv_path, backup_path)
        
        # Save new file
        with open(csv_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate CSV structure
        try:
            df = pd.read_csv(csv_path)
            if 'name' not in df.columns:
                raise HTTPException(
                    status_code=400, 
                    detail="CSV must contain a 'name' column with resort names"
                )
            
            resort_count = len(df)
            sample_names = df['name'].head(5).tolist()
            
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid CSV format: {str(e)}"
            )
        
        return {
            "status": "success",
            "message": "Official resort database updated successfully",
            "data": {
                "filename": file.filename,
                "resort_count": resort_count,
                "sample_resorts": sample_names,
                "uploaded_at": datetime.utcnow().isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading resort data: {str(e)}")