from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from backend.database import Base

class AnalysisRecord(Base):
    """
    SQLAlchemy ORM Model representing the 'analysis_history' table in our database.
    This saves every user input and the AI's exact verdict.
    """
    __tablename__ = "analysis_history"

    # Primary key for unique identification
    id = Column(Integer, primary_key=True, index=True)
    
    # Store the original text the user submitted
    original_text = Column(Text, nullable=False)
    
    # Store the AI's predicted metrics
    truth_score = Column(Float, nullable=False)
    deception_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    emotion = Column(String(50), nullable=False)
    
    # Automatically generate a timestamp when the record is created
    created_at = Column(DateTime, default=datetime.utcnow)

class TrainingData(Base):
    """
    SQLAlchemy ORM Model for Human-In-The-Loop (HITL) continuous learning.
    Stores the user-verified ground truth for future model retraining.
    """
    __tablename__ = "training_data"

    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text, nullable=False)
    
    # Ground truth label: 0 for Truthful, 1 for Deceptive
    ground_truth = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)