"""
Core API configuration and dependencies

Contains shared dependencies, middleware, and configuration for all API endpoints.
"""

import time
import uuid
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from shared.logger import get_logger, set_request_context, clear_request_context
from shared.config import settings

logger = get_logger(__name__)

# Database configuration
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="AI Dev Agent API",
        description="AI-powered development agent for automated bug fixing and analysis",
        version="1.0.0"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all HTTP requests with timing and context"""
        # Set request context for logging
        set_request_context()
        
        start_time = time.time()
        method = request.method
        path = request.url.path
        
        logger.info(
            f"→ Incoming {method} {path} from {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            logger.log_api_request(
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
            return response
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"← Request {method} {path} failed - error={str(e)} duration_ms={duration_ms:.2f}"
            )
            raise
        finally:
            clear_request_context()
    
    # Configure static files
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists() and frontend_dist.is_dir():
        logger.info(f"Mounting static files from {frontend_dist}")
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="static-assets")
    else:
        logger.warning(f"Frontend dist directory not found at {frontend_dist}")
    
    return app