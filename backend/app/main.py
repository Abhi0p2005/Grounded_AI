"""FastAPI application factory and main entry point."""
import logging
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db import check_db_health, check_vector_extension
from app.schemas import ErrorResponse, HealthResponse
from app.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting GroundedAI application...")
    
    # Check database connectivity
    if not check_db_health():
        logger.error("Database connection failed!")
    else:
        logger.info("Database connection OK")
    
    # Check pgvector extension
    if not check_vector_extension():
        logger.warning("pgvector extension not found!")
    else:
        logger.info("pgvector extension OK")
    
    yield
    
    logger.info("Shutting down GroundedAI application...")


# Create FastAPI app
app = FastAPI(
    title="GroundedAI",
    description="Domain-agnostic, config-driven knowledge copilot platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error={
                "code": f"http_{exc.status_code}",
                "message": exc.detail,
            }
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error={
                "code": "internal_error",
                "message": "An internal error occurred",
            }
        ).model_dump(),
    )


# Health check endpoint
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    db_ok = check_db_health()
    vector_ok = check_vector_extension()
    
    # Check Redis
    redis_ok = False
    try:
        r = redis.from_url(settings.redis_url, decode_responses=True)
        r.ping()
        redis_ok = True
        r.close()
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
    
    # Check LLM configuration
    llm_configured = bool(settings.google_api_key and settings.google_api_key != "your_google_ai_studio_api_key_here")
    
    status = "ok" if (db_ok and redis_ok and vector_ok and llm_configured) else "degraded"
    
    return HealthResponse(
        status=status,
        db="ok" if db_ok else "error",
        redis="ok" if redis_ok else "error",
        vector_extension=vector_ok,
        llm_configured=llm_configured,
    )


# Import and include routers (will be added in later steps)
# from app.api import workspaces, documents, chat, logs, evals
# app.include_router(workspaces.router, prefix="/api/workspaces", tags=["workspaces"])
# app.include_router(documents.router, prefix="/api/workspaces", tags=["documents"])
# app.include_router(chat.router, prefix="/api/workspaces", tags=["chat"])
# app.include_router(logs.router, prefix="/api/workspaces", tags=["logs"])
# app.include_router(evals.router, prefix="/api/workspaces", tags=["evals"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "GroundedAI",
        "version": "1.0.0",
        "docs": "/docs",
    }
