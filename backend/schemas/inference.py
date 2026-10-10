from pydantic import BaseModel, Field
from typing import Literal

class AnalysisResponse(BaseModel):
    """
    Schema for the main response returned by the /analyze endpoint.
    """
    truth_score: float = Field(..., ge=0.0, le=1.0)
    deception_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    emotion: Literal["happy", "nervous", "aggressive", "neutral", "unknown"]

class ErrorResponse(BaseModel):
    """
    Standardized error schema for consistent client-side exception handling.
    """
    error: str
    details: str

class HealthResponse(BaseModel):
    """
    Schema for the /health endpoint.
    """
    status: str
    service: str = "DeceptionAI API"
    version: str = "1.0.0"