from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func ,JSON, ForeignKey
from sqlalchemy.orm import relationship
from db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(Text)
    platform_id = Column(Integer, ForeignKey("platforms.id"))
    external_id = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    platform_rel = relationship("Platform", back_populates="users")
    flagged_posts = relationship("FlaggedPost", back_populates="user_rel")
    
class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"
    id = Column(Integer, primary_key=True)
    task_type = Column(Text)
    input_source = Column(Text)
    status = Column(Text, default="pending")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True))
    result = Column(JSON)
    flagged_posts = relationship("FlaggedPost", back_populates="task_rel")
    alerts = relationship("Alert", back_populates="task_rel")


class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(Integer, primary_key=True)
    keyword = Column(Text, unique=True)
    category = Column(Text)
    risk_weight = Column(Integer)
    evidence = relationship("Evidence", back_populates="keyword_rel")

class Platform(Base):
    __tablename__ = "platforms"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text)
    flagged_posts = relationship("FlaggedPost", back_populates="platform_rel")
    users = relationship("User", back_populates="platform_rel")
    alerts = relationship("Alert", back_populates="platform_rel")


class FlaggedPost(Base):
    __tablename__ = "flagged_posts"
    id = Column(Integer, primary_key=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    message_text = Column(Text)
    date = Column(TIMESTAMP(timezone=True), server_default=func.now())
    flagged_reason = Column(Text)
    risk_score = Column(Integer)
    screenshot_path = Column(Text)
    takedown_recommendation = Column(Text)
    task_id = Column(Integer, ForeignKey("analysis_tasks.id"))
    
    # Change these relationship arguments from a class name to a string literal
    platform_rel = relationship("Platform", back_populates="flagged_posts")
    user_rel = relationship("User", back_populates="flagged_posts")
    task_rel = relationship("AnalysisTask", back_populates="flagged_posts")
    evidence = relationship("Evidence", back_populates="post_rel")
    alerts = relationship("Alert", back_populates="post_rel")

class FakeHotel(Base):
    __tablename__ = "fake_hotels"
    id = Column(Integer, primary_key=True)
    claimed_name = Column(Text, nullable=False)
    website_domain = Column(Text)
    status = Column(Text)
    screenshot = Column(Text)
    notes = Column(Text)
    
class OfficialResort(Base):
    __tablename__ = "official_resorts"
    id = Column(Integer, primary_key=True)
    resort_name = Column(Text, nullable=False)
    domain = Column(Text, unique=True)
    category = Column(Text)


class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("flagged_posts.id"))
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    highlighted_text = Column(Text)
    entity_type = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    post_rel = relationship("FlaggedPost", back_populates="evidence")
    keyword_rel = relationship("Keyword", back_populates="evidence")


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    message = Column(Text)
    platform_id = Column(Integer, ForeignKey("platforms.id"))
    post_id = Column(Integer, ForeignKey("flagged_posts.id"))
    task_id = Column(Integer, ForeignKey("analysis_tasks.id"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    platform_rel = relationship("Platform", back_populates="alerts")
    post_rel = relationship("FlaggedPost", back_populates="alerts")
    task_rel = relationship("AnalysisTask", back_populates="alerts")


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True)
    email = Column(Text)
    subscribed_platforms = Column(Text)
    risk_threshold = Column(Integer, default=70)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())