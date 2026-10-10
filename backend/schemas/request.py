from pydantic import BaseModel, Field
from typing import Literal

class AnalysisResponse(BaseModel):
    """
    Schema for the main response returned by the /analyze endpoint.
    Ensures strict validation of probability bounds and known emotions.
    """
    truth_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Probability score indicating truthful communication."
    )
    deception_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Probability score indicating deceptive communication."
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="The AI model's confidence in its primary prediction."
    )
    # Using Literal ensures the API strictly rejects unsupported emotions in the response
    emotion: Literal["happy", "nervous", "aggressive", "neutral", "unknown"] = Field(
        ..., 
        description="The primary emotion detected from psycholinguistic markers."
    )

    class Config:
        from_attributes = True  # Modern Pydantic v2 equivalent of orm_mode = True
        json_schema_extra = {
            "example": {
                "truth_score": 0.73,
                "deception_score": 0.27,
                "confidence": 0.81,
                "emotion": "nervous"
            }
        }

class ErrorResponse(BaseModel):
    """
    Standardized error schema for consistent client-side exception handling.
    """
    error: str = Field(
        ..., 
        description="A short, high-level summary of the error type."
    )
    details: str = Field(
        ..., 
        description="A detailed, human-readable explanation of what went wrong."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Inference failed",
                "details": "The AI model encountered an unexpected error while processing the text."
            }
        }

class HealthResponse(BaseModel):
    """
    Schema for the /health endpoint, used by orchestrators (e.g., Kubernetes) for uptime checks.
    """
    status: str = Field(
        ..., 
        description="Operational status of the API."
    )
    service: str = Field(
        default="DeceptionAI API", 
        description="The name of the service."
    )
    version: str = Field(
        default="1.0.0", 
        description="The current API version."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "service": "DeceptionAI API",
                "version": "1.0.0"
            }
        }