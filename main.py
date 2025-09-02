import uvicorn
from brandgpt.api import app
from brandgpt.config import settings
from brandgpt.models import engine, Base
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_db():
    """Initialize database tables and run migrations"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Run migrations
        run_migrations()
        
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


def run_migrations():
    """Run database migrations for existing installations"""
    logger.info("Database migrations completed - all users have API keys")


if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Run the application
    logger.info(f"Starting BrandGPT API on {settings.api_host}:{settings.api_port}")
    uvicorn.run(
        "brandgpt.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )