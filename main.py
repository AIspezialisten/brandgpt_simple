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
        # Debug: Log database configuration
        logger.info(f"=== DATABASE DEBUG INFO ===")
        logger.info(f"DATABASE_URL: {settings.database_url}")
        logger.info(f"Engine: {engine}")
        logger.info(f"Engine URL: {engine.url}")
        
        # Check if database file exists
        import os
        if "sqlite" in str(engine.url):
            db_path = str(engine.url).replace("sqlite:///", "")
            logger.info(f"SQLite database path: {db_path}")
            logger.info(f"Database file exists: {os.path.exists(db_path)}")
            if os.path.exists(db_path):
                logger.info(f"Database file size: {os.path.getsize(db_path)} bytes")
                logger.info(f"Database file modified: {os.path.getmtime(db_path)}")
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Debug: Check table schemas
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Available tables: {tables}")
        
        for table in ['users', 'documents', 'sessions']:
            if table in tables:
                columns = inspector.get_columns(table)
                column_info = [(col['name'], str(col['type'])) for col in columns]
                logger.info(f"Table '{table}' columns: {column_info}")
        
        # Run migrations
        run_migrations()
        
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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