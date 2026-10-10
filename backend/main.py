import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Database imports
from backend.database import engine, Base

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("deception_ai_backend")

# --- Lifecycle Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    """
    logger.info("🚀 DeceptionAI backend is starting...")
    
    # Initialize the database (Creates tables if they don't exist yet)
    logger.info("📦 Initializing database and ensuring tables exist...")
    Base.metadata.create_all(bind=engine)
    
    logger.info("Pre-loading NLP models and resources...")
    # Transformers model will lazy-load on first request via inference.py
    
    yield  # Application is running
    
    logger.info("🛑 Shutting down DeceptionAI backend...")

# --- FastAPI Initialization ---
app = FastAPI(
    title="DeceptionAI API",
    description="AI-powered deception detection and psychological text analysis API.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Error Handling ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled system error on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "details": "Something went wrong while processing the request. Please try again later."
        }
    )

# --- Route Registration ---
try:
    from backend.routes.analyze import router as analyze_router
    app.include_router(analyze_router, prefix="/api/v1", tags=["Analysis"])
    logger.info("✅ Successfully registered /api/v1/analyze routes")
except ImportError as e:
    logger.warning(f"⚠️ Analyze router not found. Skipping route registration. Error: {e}")

# --- System Routes ---
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "service": "DeceptionAI API",
        "version": app.version
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)