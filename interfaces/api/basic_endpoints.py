"""
Basic API endpoints and frontend serving

Handles root endpoints, health checks, and SPA serving.
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["basic"])


@router.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "service": "AI Dev Agent",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "analyze": "/api/analyze",
            "webhook": "/api/webhook"
        }
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@router.get("/")
async def serve_frontend():
    """Serve the React frontend or API info"""
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    index_file = frontend_dist / "index.html"
    
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        return {
            "service": "AI Dev Agent",
            "version": "1.0.0",
            "status": "running",
            "note": "Frontend not built. Run 'cd frontend && npm run build' to build the frontend.",
            "endpoints": {
                "health": "/health",
                "analyze": "/api/analyze",
                "webhook": "/api/webhook",
                "docs": "/docs"
            }
        }


@router.get("/{full_path:path}", response_class=FileResponse)
async def serve_spa_routes(full_path: str):
    """Catch-all route to serve React SPA for client-side routing (excludes /api paths)"""
    # Don't serve SPA for API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    index_file = frontend_dist / "index.html"
    
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        raise HTTPException(status_code=404, detail="Not found")