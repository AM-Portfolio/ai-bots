"""
Main HTTP API application

Modular FastAPI application that combines all endpoint modules.
This replaces the original monolithic http_api.py file.
"""

from fastapi import FastAPI

from interfaces.api.core import create_app
from interfaces.api import (
    basic_endpoints,
    llm_endpoints,
    test_endpoints,
    doc_endpoints,
    analysis_endpoints,
    chat_endpoints,
    commit_endpoints,
    voice_endpoints
)
from interfaces.services_api import router as services_router
from interfaces.vector_db_api import router as vector_db_router, initialize_vector_db
from interfaces.translation_api import router as translation_router
from interfaces.azure_test_api import router as azure_test_router
from interfaces.unified_ai_api import router as unified_ai_router
from shared.logger import get_logger

logger = get_logger(__name__)

# Create the main FastAPI application
app = create_app()


# Startup event to initialize Vector DB
@app.on_event("startup")
async def startup_vector_db():
    """Initialize Vector DB system on startup"""
    try:
        logger.info("🚀 Application startup - initializing Vector DB...")
        success = await initialize_vector_db()
        if success:
            logger.info("✅ Vector DB initialization complete")
        else:
            logger.error("❌ Vector DB initialization failed")
    except Exception as e:
        logger.error(f"❌ Vector DB startup error: {e}", exc_info=True)


# Include all modular routers
app.include_router(basic_endpoints.router)
app.include_router(llm_endpoints.router)
app.include_router(test_endpoints.router)
app.include_router(doc_endpoints.router)
app.include_router(analysis_endpoints.router)
app.include_router(chat_endpoints.router)
app.include_router(commit_endpoints.router)
app.include_router(voice_endpoints.router)

# Include existing service routers
app.include_router(services_router)
app.include_router(vector_db_router)
app.include_router(translation_router)
app.include_router(azure_test_router)
app.include_router(unified_ai_router)

logger.info("✅ Modular HTTP API application initialized")
logger.info("📋 Registered endpoints:")
logger.info("   • Basic endpoints (/, /health, /api)")
logger.info("   • LLM testing (/api/test/llm, /api/orchestration/stream)")
logger.info("   • Integration testing (/api/test/*)")
logger.info("   • Documentation (/api/generate-docs, /api/docs/orchestrate)")
logger.info("   • Analysis (/api/analyze, /api/webhook)")
logger.info("   • Chat management (/api/chat/*)")
logger.info("   • Commit workflow (/api/commit/*)")
logger.info("   • Voice assistant (/api/voice/*)")
logger.info("   • Services management (/api/services/*)")
logger.info("   • Vector DB (/api/vector-db/*)")
logger.info("   • Translation (/api/translation/*)")
logger.info("   • Azure testing (/api/azure/*)")
logger.info("   • Unified AI (cloud-agnostic) (/api/ai/*)")