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
    from brandgpt.models.database import SessionLocal
    from brandgpt.models.user import User
    
    db = SessionLocal()
    try:
        # Migration: Generate API keys for users who don't have them
        users_without_keys = db.query(User).filter(
            (User.api_key == None) | (User.api_key == "")
        ).all()
        
        if users_without_keys:
            logger.info(f"Generating API keys for {len(users_without_keys)} existing users")
            for user in users_without_keys:
                user.api_key = User.generate_api_key()
                logger.info(f"Generated API key for user: {user.username}")
            
            db.commit()
            logger.info("API key migration completed successfully")
        else:
            logger.info("All users already have API keys")
            
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


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