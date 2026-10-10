import logging
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

# Database & Security imports
from backend.database import get_db
from backend.models import AnalysisRecord, TrainingData
from backend.security import verify_api_key

# --- Logging Configuration ---
logger = logging.getLogger("deception_ai_backend.routes.analyze")
router = APIRouter()

# --- Schemas ---
try:
    from backend.schemas.inference import AnalysisResponse
    from backend.schemas.request import AnalyzeRequest
except ImportError:
    class AnalyzeRequest(BaseModel):
        text: str = Field(..., description="The input text to analyze.")

class FeedbackRequest(BaseModel):
    """Schema for incoming Continuous Learning feedback."""
    text: str = Field(..., description="The original text analyzed.")
    label: int = Field(..., description="Ground truth label: 0 for Truthful, 1 for Deceptive.")

# --- Inference Dependency ---
try:
    from backend.services.inference import predict
except ImportError:
    def predict(text: str) -> dict:
        return {"truth_score": 0.73, "deception_score": 0.27, "confidence": 0.81, "emotion": "nervous"}


# --- Routes ---

# Notice the new `api_key: str = Depends(verify_api_key)` parameter!
# This forces FastAPI to run our security check before it even looks at the text.

@router.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_text_endpoint(
    request: AnalyzeRequest, 
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key) 
):
    """
    Accepts user text, validates it, runs AI inference, and saves the result to the database.
    Secured via API Key.
    """
    clean_text = request.text.strip()
    
    if not clean_text or len(clean_text) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text is too short. Please provide at least 10 characters."
        )

    logger.info(f"Initiating deception analysis for text length: {len(clean_text)}")

    try:
        # 1. Run AI Inference
        result = predict(clean_text)
        
        # 2. Format Response
        truth = float(result.get("truth_score", 0.0))
        deception = float(result.get("deception_score", 0.0))
        conf = float(result.get("confidence", 0.0))
        emotion = str(result.get("emotion", "unknown")).lower()
        
        # 3. Save to Database!
        db_record = AnalysisRecord(
            original_text=clean_text,
            truth_score=truth,
            deception_score=deception,
            confidence=conf,
            emotion=emotion
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        return {
            "id": db_record.id,
            "truth_score": truth,
            "deception_score": deception,
            "confidence": conf,
            "emotion": emotion
        }
        
    except Exception as e:
        logger.error(f"Inference pipeline failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Inference failed", "details": str(e)}
        )


@router.get("/history", status_code=status.HTTP_200_OK)
async def get_analysis_history(
    limit: int = 10, 
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Fetches the most recent analysis records from the database.
    Secured via API Key.
    """
    records = db.query(AnalysisRecord).order_by(AnalysisRecord.created_at.desc()).limit(limit).all()
    return records

@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Accepts verified ground-truth feedback from the user.
    Saves the text and label for future model retraining.
    """
    clean_text = request.text.strip()
    
    if not clean_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text cannot be empty.")
        
    if request.label not in [0, 1]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Label must be exactly 0 (Truthful) or 1 (Deceptive).")
        
    try:
        db_record = TrainingData(
            original_text=clean_text,
            ground_truth=request.label
        )
        db.add(db_record)
        db.commit()
        
        logger.info(f"Successfully logged ground-truth feedback for text length: {len(clean_text)}")
        return {"status": "success", "message": "Training data safely logged."}
        
    except Exception as e:
        logger.error(f"Failed to log feedback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save training data."
        )