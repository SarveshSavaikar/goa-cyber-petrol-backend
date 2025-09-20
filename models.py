from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from db import Base

class FlaggedPost(Base):
    __tablename__ = "flagged_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False)  # Telegram / Instagram
    message_text = Column(Text, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    flagged_reason = Column(Text, nullable=False)
    risk_score = Column(Integer, nullable=False)  # 0-100
    author_id = Column(String(255), nullable=True)
    screenshot_path = Column(String(500), nullable=True)
    takedown_recommendation = Column(Text, nullable=False)

class FakeHotel(Base):
    __tablename__ = "fake_hotels"
    
    id = Column(Integer, primary_key=True, index=True)
    claimed_name = Column(String(255), nullable=False)
    website_domain = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False)  # ✅ Official / ❌ Fake
    screenshot = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)