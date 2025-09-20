from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import os
import pandas as pd
import shutil

from db import get_db

router = APIRouter(prefix="/settings", tags=["settings"])

class PlatformSettings(BaseModel):
    platform: str
    enabled: bool
    monitoring_keywords: List[str] = []
    risk_threshold: int = 70
    auto_flag: bool = True

class KeywordSettings(BaseModel):
    keywords: List[str]
    category: str  # scam, gambling, prostitution, fake_hotel
    risk_weight: int = 40

class MLModelConfig(BaseModel):
    model_type: str  # text_classifier, video_analyzer, ner_extractor
    enabled: bool
    confidence_threshold: float = 0.8
    model_version: str = "1.0.0"

# In-memory storage for MVP (in production, this would be in database)
PLATFORM_SETTINGS = {
    "telegram": {"enabled": True, "monitoring_keywords": ["scam", "fraud", "casino"], "risk_threshold": 70, "auto_flag": True},
    "instagram": {"enabled": True, "monitoring_keywords": ["earn money", "work from home"], "risk_threshold": 70, "auto_flag": True},
    "website": {"enabled": True, "monitoring_keywords": ["fake hotel", "resort"], "risk_threshold": 60, "auto_flag": True},
    "facebook": {"enabled": False, "monitoring_keywords": [], "risk_threshold": 70, "auto_flag": False},
    "youtube": {"enabled": False, "monitoring_keywords": [], "risk_threshold": 70, "auto_flag": False}
}

KEYWORD_SETTINGS = {
    "scam": {"keywords": ["loan", "fraud", "scam", "get rich quick", "easy money"], "risk_weight": 50},
    "gambling": {"keywords": ["casino", "betting", "lottery", "gambling", "jackpot"], "risk_weight": 60},
    "prostitution": {"keywords": ["escort", "call girl", "massage", "dating service"], "risk_weight": 70},
    "fake_hotel": {"keywords": ["resort", "hotel", "booking", "accommodation"], "risk_weight": 40}
}

@router.get("/platforms")
async def get_platform_settings():
    """
    Get current platform monitoring settings
    """
    try:
        return {
            "status": "success",
            "data": {
                "platforms": PLATFORM_SETTINGS,
                "summary": {
                    "total_platforms": len(PLATFORM_SETTINGS),
                    "enabled_platforms": len([p for p in PLATFORM_SETTINGS.values() if p["enabled"]]),
                    "disabled_platforms": len([p for p in PLATFORM_SETTINGS.values() if not p["enabled"]])
                },
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching platform settings: {str(e)}")

@router.post("/platforms/update")
async def update_platform_settings(settings: PlatformSettings):
    """
    Update platform monitoring settings
    """
    try:
        if settings.platform not in PLATFORM_SETTINGS:
            raise HTTPException(status_code=404, detail=f"Platform '{settings.platform}' not found")
        
        if settings.risk_threshold < 0 or settings.risk_threshold > 100:
            raise HTTPException(status_code=400, detail="Risk threshold must be between 0 and 100")
        
        # Update the platform settings
        PLATFORM_SETTINGS[settings.platform] = {
            "enabled": settings.enabled,
            "monitoring_keywords": settings.monitoring_keywords,
            "risk_threshold": settings.risk_threshold,
            "auto_flag": settings.auto_flag
        }
        
        return {
            "status": "success",
            "message": f"Platform settings updated for {settings.platform}",
            "data": {
                "platform": settings.platform,
                "updated_settings": PLATFORM_SETTINGS[settings.platform],
                "updated_at": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating platform settings: {str(e)}")

@router.get("/keywords")
async def get_keyword_settings():
    """
    Get current keyword detection settings
    """
    try:
        # Flatten keywords for easy viewing
        all_keywords = []
        for category, data in KEYWORD_SETTINGS.items():
            for keyword in data["keywords"]:
                all_keywords.append({
                    "keyword": keyword,
                    "category": category,
                    "risk_weight": data["risk_weight"]
                })
        
        return {
            "status": "success",
            "data": {
                "keyword_categories": KEYWORD_SETTINGS,
                "all_keywords": all_keywords,
                "summary": {
                    "total_categories": len(KEYWORD_SETTINGS),
                    "total_keywords": len(all_keywords)
                },
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching keyword settings: {str(e)}")

@router.post("/keywords/update")
async def update_keyword_settings(settings: KeywordSettings):
    """
    Update keyword detection settings for a category
    """
    try:
        if settings.risk_weight < 0 or settings.risk_weight > 100:
            raise HTTPException(status_code=400, detail="Risk weight must be between 0 and 100")
        
        if not settings.keywords:
            raise HTTPException(status_code=400, detail="Keywords list cannot be empty")
        
        # Update the keyword settings
        KEYWORD_SETTINGS[settings.category] = {
            "keywords": settings.keywords,
            "risk_weight": settings.risk_weight
        }
        
        return {
            "status": "success",
            "message": f"Keyword settings updated for category: {settings.category}",
            "data": {
                "category": settings.category,
                "updated_settings": KEYWORD_SETTINGS[settings.category],
                "updated_at": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating keyword settings: {str(e)}")

@router.post("/keywords/add_category")
async def add_keyword_category(settings: KeywordSettings):
    """
    Add a new keyword category
    """
    try:
        if settings.category in KEYWORD_SETTINGS:
            raise HTTPException(status_code=400, detail=f"Category '{settings.category}' already exists")
        
        if settings.risk_weight < 0 or settings.risk_weight > 100:
            raise HTTPException(status_code=400, detail="Risk weight must be between 0 and 100")
        
        if not settings.keywords:
            raise HTTPException(status_code=400, detail="Keywords list cannot be empty")
        
        # Add new category
        KEYWORD_SETTINGS[settings.category] = {
            "keywords": settings.keywords,
            "risk_weight": settings.risk_weight
        }
        
        return {
            "status": "success",
            "message": f"New keyword category added: {settings.category}",
            "data": {
                "category": settings.category,
                "settings": KEYWORD_SETTINGS[settings.category],
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding keyword category: {str(e)}")

@router.delete("/keywords/category/{category}")
async def delete_keyword_category(category: str):
    """
    Delete a keyword category
    """
    try:
        if category not in KEYWORD_SETTINGS:
            raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
        
        # Don't allow deletion of core categories
        core_categories = ["scam", "gambling", "prostitution", "fake_hotel"]
        if category in core_categories:
            raise HTTPException(
                status_code=400, 
                detail=f"Core category '{category}' cannot be deleted"
            )
        
        deleted_settings = KEYWORD_SETTINGS.pop(category)
        
        return {
            "status": "success",
            "message": f"Keyword category deleted: {category}",
            "data": {
                "deleted_category": category,
                "deleted_settings": deleted_settings,
                "deleted_at": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting keyword category: {str(e)}")

@router.post("/ml/model/update")
async def update_ml_model_config(config: MLModelConfig):
    """
    Update ML model configuration (placeholder for future implementation)
    """
    try:
        # In production, this would:
        # 1. Update model configuration in database
        # 2. Deploy new model version if needed
        # 3. Update model parameters and thresholds
        
        if config.confidence_threshold < 0.0 or config.confidence_threshold > 1.0:
            raise HTTPException(
                status_code=400, 
                detail="Confidence threshold must be between 0.0 and 1.0"
            )
        
        valid_model_types = ["text_classifier", "video_analyzer", "ner_extractor"]
        if config.model_type not in valid_model_types:
            raise HTTPException(
                status_code=400,
                detail=f"Model type must be one of: {valid_model_types}"
            )
        
        return {
            "status": "success",
            "message": f"ML model configuration updated: {config.model_type}",
            "data": {
                "model_type": config.model_type,
                "enabled": config.enabled,
                "confidence_threshold": config.confidence_threshold,
                "model_version": config.model_version,
                "updated_at": datetime.utcnow().isoformat(),
                "note": "This is an MVP implementation - actual ML models will be integrated in production"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating ML model config: {str(e)}")

@router.get("/export")
async def export_settings():
    """
    Export all settings as JSON
    """
    try:
        settings_export = {
            "platforms": PLATFORM_SETTINGS,
            "keywords": KEYWORD_SETTINGS,
            "export_metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "system": "Goa Cyber Patrol"
            }
        }
        
        return {
            "status": "success",
            "data": settings_export
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting settings: {str(e)}")

@router.post("/import")
async def import_settings(file: UploadFile = File(...)):
    """
    Import settings from JSON file
    """
    try:
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="File must be a JSON file")
        
        # Read and parse JSON
        content = await file.read()
        try:
            settings_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        
        # Validate and update settings
        if "platforms" in settings_data:
            PLATFORM_SETTINGS.update(settings_data["platforms"])
        
        if "keywords" in settings_data:
            KEYWORD_SETTINGS.update(settings_data["keywords"])
        
        return {
            "status": "success",
            "message": "Settings imported successfully",
            "data": {
                "imported_platforms": len(settings_data.get("platforms", {})),
                "imported_keyword_categories": len(settings_data.get("keywords", {})),
                "imported_at": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing settings: {str(e)}")