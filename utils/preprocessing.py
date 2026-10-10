import re
import logging
from typing import Dict, Any, Union, Optional

# --- Configuration & Logging ---
logger = logging.getLogger("deception_ai.utils.preprocessing")

# A lightweight dictionary for expanding common English contractions
CONTRACTIONS = {
    "don't": "do not", "can't": "cannot", "won't": "will not", 
    "it's": "it is", "i'm": "i am", "you're": "you are", 
    "they're": "they are", "we're": "we are", "didn't": "did not", 
    "isn't": "is not", "aren't": "are not", "hasn't": "has not", 
    "haven't": "have not", "doesn't": "does not", "wasn't": "was not", 
    "weren't": "were not", "i've": "i have", "you've": "you have", 
    "they've": "they have", "we've": "we have", "i'll": "i will", 
    "you'll": "you will", "he'll": "he will", "she'll": "she will",
    "that's": "that is", "there's": "there is", "what's": "what is"
}

def clean_text(text: str) -> str:
    """
    Cleans text by stripping whitespace and normalizing spacing.
    Preserves the fundamental meaning and structure of the input.
    
    Args:
        text (str): Raw input string.
        
    Returns:
        str: Cleaned string. Returns empty string if input is None or invalid.
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Strip leading/trailing whitespace
    text = text.strip()
    # Replace multiple spaces, tabs, or newlines with a single space
    text = re.sub(r'\s+', ' ', text)
    
    return text

def remove_noise(text: str) -> str:
    """
    Removes noisy elements like URLs, emails, and non-standard special characters
    while preserving standard punctuation required for NLP context.
    
    Args:
        text (str): Input string.
        
    Returns:
        str: String with noise removed.
    """
    if not text:
        return ""
        
    # Remove URLs (http, https, www)
    text = re.sub(r'http[s]?://\S+|www\.\S+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+\.\S+', '', text)
    
    # Remove weird special characters but preserve standard punctuation and alphanumeric chars
    # Preserved: periods, commas, exclamation marks, question marks, quotes, hyphens
    text = re.sub(r'[^\w\s\.,!?\'"-]', '', text)
    
    return clean_text(text)  # Clean up any residual spaces left by regex

def normalize_text(text: str, lowercase: bool = True) -> str:
    """
    Normalizes text by optionally lowercasing and expanding common contractions.
    
    Args:
        text (str): Input string.
        lowercase (bool): Whether to convert text to lowercase. Defaults to True.
        
    Returns:
        str: Normalized string.
    """
    if not text:
        return ""
        
    if lowercase:
        text = text.lower()
        
        # Expand contractions (only reliable if text is lowercased)
        for contraction, expansion in CONTRACTIONS.items():
            # Use word boundaries to avoid replacing substrings inside words
            text = re.sub(rf"\b{contraction}\b", expansion, text)
            
    return text

def validate_text(text: str, min_length: int = 10) -> bool:
    """
    Validates if the text is substantial enough for meaningful NLP inference.
    
    Args:
        text (str): Input string.
        min_length (int): Minimum number of valid characters required.
        
    Returns:
        bool: True if text is valid and meets length requirements, False otherwise.
    """
    if not text or not isinstance(text, str):
        return False
        
    cleaned = clean_text(text)
    return len(cleaned) >= min_length

def tokenize_text(text: str, tokenizer: Any, max_length: int = 512) -> Dict[str, Any]:
    """
    Tokenizes the text using a Hugging Face tokenizer with standard padding and truncation.
    
    Args:
        text (str): Cleaned and normalized string.
        tokenizer (Any): Pre-trained Hugging Face tokenizer instance.
        max_length (int): Maximum token sequence length.
        
    Returns:
        Dict[str, Any]: Dictionary containing 'input_ids' and 'attention_mask' as PyTorch tensors.
    """
    if not text:
        logger.warning("Empty text passed to tokenizer.")
    
    encoded = tokenizer(
        text,
        truncation=True,
        padding="max_length",
        max_length=max_length,
        return_tensors="pt"
    )
    
    return encoded

def preprocess_pipeline(
    text: str, 
    tokenizer: Optional[Any] = None, 
    max_length: int = 512, 
    lowercase: bool = True
) -> Union[str, Dict[str, Any]]:
    """
    End-to-end preprocessing pipeline. Safely cleans, removes noise, normalizes, 
    and optionally tokenizes the raw input text.
    
    Args:
        text (str): Raw user input.
        tokenizer (Optional[Any]): Hugging Face tokenizer. If provided, returns encoded dict.
        max_length (int): Maximum sequence length for tokenization.
        lowercase (bool): Whether to lowercase the text during normalization.
        
    Returns:
        Union[str, Dict]: Tokenized dictionary if tokenizer is provided, else cleaned string.
    """
    # 1. Validation check
    if not validate_text(text, min_length=1):
        logger.warning("Preprocessing pipeline received empty or invalid text.")
        text = ""  # Force safe fallback
        
    # 2. Sequential Cleaning & Normalization
    processed_text = clean_text(text)
    processed_text = remove_noise(processed_text)
    processed_text = normalize_text(processed_text, lowercase=lowercase)
    
    # 3. Optional Tokenization
    if tokenizer is not None:
        return tokenize_text(processed_text, tokenizer, max_length=max_length)
        
    return processed_text