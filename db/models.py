from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, index=True)
    title = Column(String(500))
    description = Column(Text)
    source = Column(String(50))
    severity = Column(String(50))
    status = Column(String(50), default="open")
    extra_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    analyses = relationship("Analysis", back_populates="issue")


class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"))
    root_cause = Column(Text)
    confidence_score = Column(Float)
    affected_components = Column(JSON)
    analysis_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    issue = relationship("Issue", back_populates="analyses")
    fixes = relationship("Fix", back_populates="analysis")


class Fix(Base):
    __tablename__ = "fixes"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"))
    file_path = Column(String(500))
    original_code = Column(Text)
    fixed_code = Column(Text)
    explanation = Column(Text)
    test_code = Column(Text)
    pr_url = Column(String(500))
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    analysis = relationship("Analysis", back_populates="fixes")
