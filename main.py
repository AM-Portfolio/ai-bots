import uvicorn
import logging
from contextlib import asynccontextmanager
from sqlalchemy import create_engine

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
    port = settings.port
    logger.info(f"Starting server on {settings.app_host}:{port}")
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )
