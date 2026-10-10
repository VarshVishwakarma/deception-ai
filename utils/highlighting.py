import re
import logging
from typing import List, Dict, Any

# --- Configuration & Logging ---
logger = logging.getLogger("deception_ai.utils.highlighting")

# Centralized CSS style for highlighted spans to ensure consistent, premium UI
HIGHLIGHT_STYLE = (
    "background-color: rgba(239, 68, 68, 0.2); "
    "color: #FCA5A5; "
    "padding: 2px 6px; "
    "border-radius: 4px; "
    "border: 1px dashed rgba(239, 68, 68, 0.5); "
    "font-weight: 600;"
)

def get_suspicious_keywords() -> List[str]:
    """
    Returns a curated, easily extendable list of psycholinguistic keywords 
    and phrases frequently associated with deceptive or high-cognitive-load text.
    
    Returns:
        List[str]: A list of suspicious trigger phrases.
    """
    return [
        "honestly", "trust me", "believe me", "to be frank", 
        "to be honest", "to tell the truth", "literally", 
        "actually", "i swear", "in all honesty", "frankly",
        "as a matter of fact", "to be perfectly honest"
    ]

def detect_suspicious_phrases(text: str) -> List[str]:
    """
    Scans the input text for occurrences of suspicious keywords.
    Case-insensitive and uses word boundaries to prevent partial matches.
    
    Args:
        text (str): The raw input text.
        
    Returns:
        List[str]: A list of the specific keywords that were found in the text.
    """
    if not text or not isinstance(text, str):
        return []
        
    keywords = get_suspicious_keywords()
    
    # Sort by length descending to match longer phrases first 
    # (e.g., "to be honest" evaluates before "honest")
    keywords = sorted(keywords, key=len, reverse=True)
    
    detected = set()
    for kw in keywords:
        pattern = rf'\b{re.escape(kw)}\b'
        if re.search(pattern, text, flags=re.IGNORECASE):
            detected.add(kw.lower())
            
    return list(detected)

def highlight_text(text: str, keywords: List[str]) -> str:
    """
    Wraps detected keywords in the text with styled HTML spans.
    Uses a single-pass regex substitution to safely handle formatting 
    without breaking previous HTML tags.
    
    Args:
        text (str): The original input text.
        keywords (List[str]): A list of keywords known to be in the text.
        
    Returns:
        str: The HTML-formatted text safe for Streamlit markdown rendering.
    """
    if not text or not keywords:
        return text
        
    # Sort keywords by length descending to avoid double-wrapping overlapping phrases
    sorted_keywords = sorted(keywords, key=len, reverse=True)
    escaped_kws = [re.escape(kw) for kw in sorted_keywords]
    
    # Compile a single regex OR pattern: \b(phrase one|phrase two)\b
    pattern = re.compile(rf'\b({"|".join(escaped_kws)})\b', flags=re.IGNORECASE)
    
    # Replacement callback to preserve the user's original capitalization
    def replacement_callback(match):
        original_text = match.group(1)
        return f'<span style="{HIGHLIGHT_STYLE}">{original_text}</span>'
        
    highlighted_text = pattern.sub(replacement_callback, text)
    return highlighted_text

def apply_highlighting(text: str) -> str:
    """
    End-to-end highlighting pipeline. Fetches keywords, detects matches, 
    and applies the HTML styling in one clean operation.
    
    Args:
        text (str): The raw input text.
        
    Returns:
        str: Fully processed and highlighted HTML string.
    """
    if not text or not isinstance(text, str):
        return ""
        
    detected_phrases = detect_suspicious_phrases(text)
    
    if not detected_phrases:
        return text
        
    return highlight_text(text, detected_phrases)

def get_highlight_summary(text: str) -> Dict[str, Any]:
    """
    Generates metadata about the detected suspicious patterns for use in 
    UI metrics and alerting.
    
    Args:
        text (str): The raw input text.
        
    Returns:
        Dict[str, Any]: A summary containing the count and list of matched phrases.
    """
    if not text or not isinstance(text, str):
        return {"count": 0, "phrases": []}
        
    detected = detect_suspicious_phrases(text)
    
    return {
        "count": len(detected),
        "phrases": detected
    }