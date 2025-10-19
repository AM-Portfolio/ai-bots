import uvicorn
import logging
import os
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from pathlib import Path

from interfaces.http_api import app
from interfaces.vector_db_api import initialize_vector_db
from observability.metrics import metrics
from db.models import Base
from shared.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def verify_env_loaded():
    """Verify that .env file is loaded and log configuration status."""
    env_file = Path(".env")
    
    if env_file.exists():
        logger.info("✅ .env file found and loaded")
    else:
        logger.warning("⚠️  .env file not found, using defaults and environment variables")
    
    # Log configuration status (without exposing secrets)
    logger.info("🔧 Configuration loaded:")
    logger.info(f"   • Environment: {settings.environment}")
    logger.info(f"   • LLM Provider: {settings.llm_provider}")
    logger.info(f"   • Together Model: {settings.together_model}")
    logger.info(f"   • Together API Key: {'✓ Configured' if settings.together_api_key else '✗ Missing'}")
    logger.info(f"   • GitHub Token: {'✓ Configured' if settings.github_token else '✗ Missing'}")
    logger.info(f"   • GitHub Org: {settings.github_org or 'Not set'}")
    logger.info(f"   • Database: {settings.database_url.split('://')[0]}://...")
    logger.info(f"   • Vector DB: {settings.vector_db_provider} (fallback: {settings.vector_db_fallback_enabled})")
    logger.info(f"   • Host: {settings.app_host}:{settings.app_port}")
    logger.info(f"   • Log Level: {settings.log_level}")
    
    # Check for critical missing values
    missing = []
    if not settings.together_api_key:
        missing.append("TOGETHER_API_KEY")
    if not settings.github_token:
        missing.append("GITHUB_TOKEN")
    
    if missing:
        logger.warning(f"⚠️  Missing configuration: {', '.join(missing)}")
    else:
        logger.info("✅ All critical configuration values present")


def init_database():
    logger.info("Initializing database...")
    try:
        engine = create_engine(settings.database_url, echo=False)
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
        return engine
    except Exception as e:
        logger.warning(f"Database initialization skipped: {e}")
        return None


@asynccontextmanager
async def lifespan(app):
    logger.info("Starting AI Dev Agent...")
    
    # Verify environment configuration is loaded
    verify_env_loaded()
    
    # Initialize database
    init_database()
    
    # Initialize Vector DB system
    logger.info("Initializing Vector DB...")
    await initialize_vector_db()
    
    port = settings.port
    logger.info(f"AI Dev Agent ready on {settings.app_host}:{port}")
    yield
    logger.info("Shutting down AI Dev Agent...")


app.router.lifespan_context = lifespan


@app.get("/metrics")
async def get_metrics():
    return metrics.get_metrics()


if __name__ == "__main__":
    # Load and verify configuration
    verify_env_loaded()
    
    port = settings.port
    logger.info(f"Starting server on {settings.app_host}:{port}")
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )
