import logging
import re
from typing import Dict, Any, Tuple

# --- Logging Configuration ---
logger = logging.getLogger("deception_ai_backend.services.inference")

# --- Lazy Loading Globals ---
_MODEL = None
_TOKENIZER = None
_DEVICE = None

# --- Custom Model Config ---
# We are swapping out the generic model for your custom-trained AI!
# This points directly to the folder where train.py saved your model.
MODEL_NAME = "model/saved_model/"
FALLBACK_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"

def _get_device() -> Any:
    """
    Detects and returns the optimal hardware device for inference.
    Supports CUDA (NVIDIA), MPS (Apple Silicon), and CPU fallback.
    """
    import torch
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")

def _load_model_lazily() -> None:
    """
    Loads the Hugging Face model and tokenizer globally exactly once.
    Implements the Singleton pattern via lazy loading to save memory and startup time.
    """
    global _MODEL, _TOKENIZER, _DEVICE
    
    if _MODEL is not None and _TOKENIZER is not None:
        return

    try:
        import torch
        import os
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        
        _DEVICE = _get_device()
        logger.info(f"Hardware acceleration selected: {_DEVICE}")
        
        # 🐛 BUG FIX: Check if the local trained model exists. If not, use the fallback internet model.
        # This prevents Docker from crashing if the folder didn't copy correctly.
        model_to_load = MODEL_NAME if os.path.exists(MODEL_NAME) else FALLBACK_MODEL
        logger.info(f"Loading transformer model '{model_to_load}' into memory...")
        
        _TOKENIZER = AutoTokenizer.from_pretrained(model_to_load)
        _MODEL = AutoModelForSequenceClassification.from_pretrained(model_to_load)
        
        _MODEL.to(_DEVICE)
        _MODEL.eval()  # Strictly set to evaluation mode
        logger.info(f"✅ Model '{model_to_load}' loaded successfully and set to evaluation mode.")
        
    except ImportError as e:
        logger.error(f"Missing ML dependencies (torch or transformers). {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load the model: {e}", exc_info=True)
        raise

def _preprocess_text(text: str) -> str:
    """
    Cleans and normalizes the input text prior to tokenization.
    """
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def _detect_emotion(text: str) -> str:
    """
    A fast, heuristic-based emotion classifier using psycholinguistic keyword matching.
    Acts as a lightweight supplement to the main transformer model.
    """
    text_lower = text.lower()
    
    nervous_markers = {"uh", "um", "maybe", "perhaps", "guess", "honestly", "kinda"}
    aggressive_markers = {"never", "absolutely", "ridiculous", "stupid", "always", "demand"}
    
    words = set(re.findall(r'\b\w+\b', text_lower))
    
    if len(words.intersection(nervous_markers)) > 0:
        return "nervous"
    elif len(words.intersection(aggressive_markers)) > 0:
        return "aggressive"
    else:
        return "neutral"

def predict(text: str) -> Dict[str, Any]:
    """
    Core inference function. Processes raw text, runs the forward pass, 
    and returns a structured psychological analysis dictionary.
    
    Args:
        text (str): The raw user input.
        
    Returns:
        dict: A structured payload containing truth_score, deception_score, 
              confidence, and emotion.
    """
    # 1. Fallback / Default Response (Safety Net)
    fallback_response = {
        "truth_score": 0.50,
        "deception_score": 0.50,
        "confidence": 0.00,
        "emotion": "unknown"
    }
    
    try:
        import torch
        import torch.nn.functional as F
        
        # 2. Preprocessing & Initialization
        clean_text = _preprocess_text(text)
        if not clean_text:
            return fallback_response
            
        _load_model_lazily()
        
        # 3. Tokenization
        inputs = _TOKENIZER(
            clean_text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(_DEVICE)
        
        # 4. Model Inference (Optimized)
        with torch.no_grad():
            outputs = _MODEL(**inputs)
            logits = outputs.logits
            
        # 5. Post-Processing & Softmax
        probabilities = F.softmax(logits, dim=-1).squeeze().cpu().numpy()
        
        # 🐛 BUG FIX: The labels were swapped! 
        # In train.py, we defined: 0 = truthful, 1 = deceptive.
        truth_prob = float(probabilities[0])
        deception_prob = float(probabilities[1])
        
        confidence = float(max(truth_prob, deception_prob))
        emotion = _detect_emotion(clean_text)
        
        # 6. Structured Output
        result = {
            "truth_score": round(truth_prob, 4),
            "deception_score": round(deception_prob, 4),
            "confidence": round(confidence, 4),
            "emotion": emotion
        }
        
        logger.debug(f"Inference complete. Scores -> Truth: {result['truth_score']}, Deception: {result['deception_score']}")
        return result
        
    except ImportError:
        logger.error("PyTorch or Transformers not installed. Returning fallback response.")
        return fallback_response
    except Exception as e:
        logger.error(f"Inference critical failure: {str(e)}", exc_info=True)
        return fallback_response