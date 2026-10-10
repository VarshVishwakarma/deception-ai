import os
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

# The name of the header we expect the frontend to send
API_KEY_NAME = "X-API-Key"

# We use a default key here so it works instantly on your machine.
# In a real production app, this would be hidden in a secret .env file!
VALID_API_KEY = os.getenv("API_KEY", "dai-secret-key-2026")

# Tell FastAPI to look for this specific header in every request
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Validates the API key attached to the incoming HTTP request.
    If it's missing or wrong, it instantly blocks the request.
    """
    if not api_key or api_key != VALID_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Invalid or missing X-API-Key header."
        )
    return api_key