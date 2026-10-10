import os
from functools import lru_cache
from typing import List, Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    # Fallback to standard Pydantic if pydantic-settings isn't installed
    from pydantic import BaseSettings
    SettingsConfigDict = dict


class Settings(BaseSettings):
    """
    Core configuration class for DeceptionAI.
    Automatically loads and parses environment variables from a .env file.
    """
    
    # --- System & Application Metadata ---
    APP_NAME: str = "DeceptionAI API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # --- API & Networking ---
    API_URL: str = "http://localhost:8000"
    API_TIMEOUT_SECONDS: int = 10
    CORS_ORIGINS: List[str] = ["*"]
    
    # --- Security & Secrets ---
    # These should ALWAYS be injected via environment variables in production.
    SECRET_KEY: Optional[str] = None
    API_KEY: Optional[str] = None

    # --- Machine Learning Model Configuration ---
    MODEL_NAME: str = "distilbert-base-uncased-finetuned-sst-2-english"
    MODEL_SAVE_PATH: str = "model/saved_model/"
    MAX_SEQ_LENGTH: int = 512
    TRAIN_BATCH_SIZE: int = 16
    EVAL_BATCH_SIZE: int = 16
    
    # --- Application Business Logic Constants ---
    THREAT_LOW_THRESHOLD: float = 0.40
    THREAT_HIGH_THRESHOLD: float = 0.70

    # --- NLP & Linguistic Constants ---
    SUSPICIOUS_KEYWORDS: List[str] = [
        "honestly", "trust me", "believe me", "to be frank", 
        "to be honest", "to tell the truth", "literally", 
        "actually", "i swear", "in all honesty", "frankly",
        "as a matter of fact", "to be perfectly honest"
    ]

    # Pydantic v2 Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" # Safely ignore extra environment variables
    )


class DevelopmentConfig(Settings):
    """Configuration overrides for local development."""
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8501"]


class ProductionConfig(Settings):
    """Configuration overrides for production deployment."""
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    # Restrict CORS to trusted frontends only
    CORS_ORIGINS: List[str] = ["https://app.deceptionai.com"]


@lru_cache()
def get_settings() -> Settings:
    """
    Factory function to retrieve the application configuration.
    Uses @lru_cache to ensure it acts as a Singleton, reading the .env file only once.
    
    Returns:
        Settings: The appropriate configuration object based on the ENVIRONMENT var.
    """
    # Peak at the environment directly to determine which config class to instantiate
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
        
    return DevelopmentConfig()

# Optional: Convenience instantiation for immediate use in smaller scripts.
# For FastAPI endpoints, it's highly recommended to use `Depends(get_settings)`.
config = get_settings()