"""
SQLAlchemy ORM Models for Stinker AI Code Reviewer
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Pattern(Base):
    """Stores learned coding patterns from repositories"""
    __tablename__ = 'patterns'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_full_name = Column(String(255), nullable=False, index=True)
    pattern_type = Column(String(100), nullable=False)
    pattern_name = Column(String(255), nullable=False)
    pattern_data = Column(Text, nullable=False)  # JSON string
    frequency = Column(Integer, default=1)
    last_seen = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_repo_pattern', 'repo_full_name', 'pattern_type', 'pattern_name', unique=True),
    )
    
    def __repr__(self):
        return f"<Pattern(repo={self.repo_full_name}, type={self.pattern_type}, name={self.pattern_name})>"


class Review(Base):
    """Stores PR review history"""
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_full_name = Column(String(255), nullable=False, index=True)
    pr_number = Column(Integer, nullable=False)
    review_data = Column(Text, nullable=False)  # JSON string
    status = Column(String(50), default='completed')
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_repo_pr', 'repo_full_name', 'pr_number', unique=True),
    )
    
    def __repr__(self):
        return f"<Review(repo={self.repo_full_name}, pr={self.pr_number}, status={self.status})>"


class RepoConfig(Base):
    """Stores repository-specific configurations"""
    __tablename__ = 'repo_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_full_name = Column(String(255), nullable=False, unique=True, index=True)
    config_data = Column(Text, nullable=False)  # JSON string
    last_analyzed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<RepoConfig(repo={self.repo_full_name})>"
