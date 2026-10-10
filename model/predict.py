import os
import sys
import time
import argparse
import logging
import re
from typing import Dict, Any, Tuple

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# --- Configuration & Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("deception_ai.predict")

SAVE_DIRECTORY = "model/saved_model/"

def get_device() -> torch.device:
    """
    Detects and returns the available hardware device for inference.
    """
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    else:
        return torch.device("cpu")

def load_model(model_dir: str = SAVE_DIRECTORY) -> Tuple[AutoModelForSequenceClassification, AutoTokenizer, torch.device]:
    """
    Loads the trained Hugging Face model and tokenizer from the specified directory.
    """
    if not os.path.exists(model_dir):
        logger.error(f"Model directory '{model_dir}' not found. Please run train.py first.")
        sys.exit(1)
        
    logger.info(f"Loading model and tokenizer from '{model_dir}'...")
    try:
        device = get_device()
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        
        model.to(device)
        model.eval()  # Set model to evaluation mode
        
        logger.info(f"✅ Model loaded successfully on {device}.")
        return model, tokenizer, device
    except Exception as e:
        logger.error(f"Failed to load the model: {str(e)}", exc_info=True)
        sys.exit(1)

def preprocess_text(text: str) -> str:
    """
    Normalizes spacing and cleans the input text before tokenization.
    """
    if not text or not isinstance(text, str):
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def detect_emotion(text: str) -> str:
    """
    A lightweight, heuristic-based emotion classifier using psycholinguistic keywords.
    """
    text_lower = text.lower()
    
    nervous_markers = {"uh", "um", "maybe", "perhaps", "guess", "honestly", "kinda", "sorta"}
    aggressive_markers = {"never", "absolutely", "ridiculous", "stupid", "always", "demand"}
    
    words = set(re.findall(r'\b\w+\b', text_lower))
    
    if len(words.intersection(nervous_markers)) > 0:
        return "nervous"
    elif len(words.intersection(aggressive_markers)) > 0:
        return "aggressive"
    else:
        return "neutral"

def predict(
    text: str, 
    model: AutoModelForSequenceClassification, 
    tokenizer: AutoTokenizer, 
    device: torch.device
) -> Dict[str, Any]:
    """
    Executes the inference pipeline on the input text.
    """
    clean_text = preprocess_text(text)
    if not clean_text:
        raise ValueError("Input text cannot be empty.")
        
    # 1. Tokenize input
    inputs = tokenizer(
        clean_text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True
    ).to(device)
    
    # 2. Run Inference
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        
    # 3. Post-processing
    probabilities = F.softmax(logits, dim=-1).squeeze().cpu().numpy()
    
    # Assuming label mapping: 0=truthful, 1=deceptive
    truth_score = float(probabilities[0])
    deception_score = float(probabilities[1])
    confidence = max(truth_score, deception_score)
    
    emotion = detect_emotion(clean_text)
    
    return {
        "truth_score": truth_score,
        "deception_score": deception_score,
        "confidence": confidence,
        "emotion": emotion
    }

def print_pretty_results(text: str, results: Dict[str, Any], elapsed_time: float):
    """
    Formats the inference output for a clean, professional CLI experience.
    """
    print("\n" + "="*50)
    print(" 👁️  DECEPTION AI - INFERENCE REPORT")
    print("="*50)
    print(f"📄 Input Text: \"{text[:75]}{'...' if len(text) > 75 else ''}\"")
    print("-" * 50)
    
    # Extract scores
    t_score = results['truth_score'] * 100
    d_score = results['deception_score'] * 100
    conf = results['confidence'] * 100
    emotion = results['emotion'].capitalize()
    
    # ANSI Color codes
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    
    print(f"🟢 Truth Probability     : {GREEN}{t_score:.2f}%{RESET}")
    print(f"🔴 Deception Probability : {RED}{d_score:.2f}%{RESET}")
    print(f"🔵 Model Confidence      : {BLUE}{conf:.2f}%{RESET}")
    print(f"🎭 Detected Emotion      : {emotion}")
    print("-" * 50)
    
    # Threat Level Indicator
    if d_score > 70:
        print(f"🚨 THREAT LEVEL: {RED}HIGH RISK (Likely Deceptive){RESET}")
    elif d_score > 40:
        print(f"⚠️ THREAT LEVEL: {BLUE}MEDIUM RISK (Anomalies Detected){RESET}")
    else:
        print(f"✅ THREAT LEVEL: {GREEN}LOW RISK (Likely Truthful){RESET}")
        
    print(f"⏱️  Inference Time        : {elapsed_time:.3f} seconds")
    print("="*50 + "\n")

def main():
    """
    CLI Entry point.
    """
    parser = argparse.ArgumentParser(description="DeceptionAI CLI Predictor")
    parser.add_argument(
        "text", 
        type=str, 
        nargs="?", 
        default="To be honestly frank with you, I was absolutely nowhere near the scene of the incident.",
        help="Text to analyze for deception patterns."
    )
    parser.add_argument(
        "--model_dir", 
        type=str, 
        default=SAVE_DIRECTORY, 
        help="Path to the trained model directory."
    )
    args = parser.parse_args()

    # Load resources
    model, tokenizer, device = load_model(args.model_dir)
    
    # Execute prediction with timing
    try:
        start_time = time.time()
        results = predict(args.text, model, tokenizer, device)
        elapsed_time = time.time() - start_time
        
        # Output
        print_pretty_results(args.text, results, elapsed_time)
        
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()