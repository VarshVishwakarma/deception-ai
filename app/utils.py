import re
import time
import logging
import requests
import os
from typing import Dict, Any, List

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 🐛 BUG FIX: Grab the URL from the Docker environment variables instead of hardcoding localhost!
API_URL = os.getenv("API_URL", "http://backend:8000/api/v1/analyze")
API_KEY = os.getenv("API_KEY", "dai-secret-key-2026")
HEADERS = {"X-API-Key": API_KEY}

# Pre-compiled keywords for faster regex scanning
MARKERS = {
    "qualifiers": ["honestly", "to be frank", "to tell the truth", "to be honest", "frankly"],
    "absolutes": ["never", "always", "absolutely", "100%", "impossible"],
    "defensive": ["trust me", "believe me", "i swear", "literally", "actually", "obviously", "just"]
}
# Flatten for quick scanning
SUSPICIOUS_KEYWORDS = [word for category in MARKERS.values() for word in category]

def check_backend_status(health_url: str = None) -> bool:
    """
    Pings the backend health endpoint to check if the API is online.
    System endpoints usually don't require an API key.
    """
    if health_url is None:
        health_url = API_URL.replace("/api/v1/analyze", "/health")
        
    try:
        response = requests.get(health_url, timeout=1.5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    cleaned = re.sub(r'\s+', ' ', text)
    return cleaned.strip()

def validate_input(text: str) -> bool:
    if not text or not isinstance(text, str):
        return False
    return len(clean_text(text)) >= 10

def extract_keywords(text: str) -> List[str]:
    if not text:
        return []
    found_words = set()
    text_lower = text.lower()
    sorted_markers = sorted(SUSPICIOUS_KEYWORDS, key=len, reverse=True)
    
    for word in sorted_markers:
        if re.search(rf'\b{re.escape(word)}\b', text_lower):
            found_words.add(word)
    return list(found_words)

def get_threat_level(score: float) -> str:
    try:
        val = float(score)
    except (ValueError, TypeError):
        return "Medium"

    if val >= 0.70:
        return "High"
    elif val >= 0.40:
        return "Medium"
    return "Low"

def generate_explanation(score: float, emotion: str, markers_found: List[str] = None) -> str:
    emotion_clean = emotion.capitalize() if isinstance(emotion, str) else "Neutral"
    markers_count = len(markers_found) if markers_found else 0
    try:
        val = float(score)
    except (ValueError, TypeError):
        val = 0.5

    if val >= 0.70:
        base = f"High deception probability detected. The subject displays <strong>'{emotion_clean}'</strong> emotional markers "
        if markers_count > 0:
            base += f"combined with {markers_count} restrictive qualifier(s) (e.g., over-justification). "
        else:
            base += "combined with structural anomalies. "
        base += "This linguistic pattern is heavily associated with high cognitive load and fabricated narratives."
        return base
    elif val >= 0.40:
        base = f"Moderate risk detected. The text contains minor baseline deviations and <strong>'{emotion_clean}'</strong> undertones. "
        if markers_count > 0:
            base += "The presence of persuasive keywords suggests an attempt to manage perception. "
        base += "Further verification and contextual cross-referencing is advised."
        return base
    else:
        base = f"Low deception risk. The statement flows with baseline truthful linguistic patterns and a <strong>'{emotion_clean}'</strong> disposition. "
        if markers_count > 0:
            base += "Despite a few colloquial qualifiers, "
        base += "the semantic structure lacks the cognitive distortion markers typical of deception."
        return base

def get_mock_response(text: str) -> Dict[str, Any]:
    extracted = extract_keywords(text)
    mock_score = 0.88 if len(extracted) > 1 else 0.45
    mock_emotion = "Defensive & Anxious" if mock_score > 0.5 else "Calm"
    return {
        "truth_score": 1.0 - mock_score,
        "deception_score": mock_score,
        "confidence_score": 0.94,
        "emotion": mock_emotion,
        "explanation": generate_explanation(mock_score, mock_emotion, extracted),
        "suspicious_words": extracted,
        "threat_level": get_threat_level(mock_score)
    }

def normalize_response(raw_data: Dict[str, Any], text: str) -> Dict[str, Any]:
    deception_score = float(raw_data.get("deception_score", 0.0))
    emotion = str(raw_data.get("emotion", "Neutral")).capitalize()
    extracted_words = extract_keywords(text)
    return {
        "truth_score": float(raw_data.get("truth_score", 0.0)),
        "deception_score": deception_score,
        "confidence_score": float(raw_data.get("confidence", 0.0)),
        "emotion": emotion,
        "threat_level": get_threat_level(deception_score),
        "suspicious_words": extracted_words,
        "explanation": generate_explanation(deception_score, emotion, extracted_words)
    }

def call_analysis_api(text: str, api_url: str = None, use_demo: bool = False) -> Dict[str, Any]:
    if api_url is None:
        api_url = API_URL
        
    if use_demo:
        return get_mock_response(text)
        
    payload = {"text": clean_text(text)}
    max_retries = 1
    timeout_seconds = 15

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(api_url, json=payload, headers=HEADERS, timeout=timeout_seconds)
            response.raise_for_status()
            
            return normalize_response(response.json(), payload["text"])
            
        except requests.exceptions.HTTPError as e:
            logger.warning(f"API HTTP Error on attempt {attempt + 1}: {e}")
            if response.status_code == 403:
                st_error = "API Key Invalid or Missing!"
                logger.error(st_error)
                raise ConnectionError(st_error)
        except Exception as e:
            logger.error(f"Unexpected API error: {e}")

        if attempt < max_retries:
            time.sleep(1.5)
            
    raise ConnectionError(f"Failed to communicate with backend at {api_url}.")


def submit_feedback(text: str, label: int) -> bool:
    """
    Submits user-verified ground truth feedback to the backend for continuous learning.
    label: 0 for Truthful, 1 for Deceptive
    """
    # Derive the /feedback URL from the existing API_URL
    feedback_url = API_URL.replace("/analyze", "/feedback")
    
    payload = {
        "text": clean_text(text),
        "label": label
    }
    
    try:
        response = requests.post(feedback_url, json=payload, headers=HEADERS, timeout=10)
        response.raise_for_status()
        logger.info(f"Feedback successfully submitted. Label: {label}")
        return True
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        return False