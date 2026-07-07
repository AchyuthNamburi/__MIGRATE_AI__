# recreate_tables.py
"""Recreate all database tables"""

from backend.core.database import engine, Base
from backend.models.user import User, UserProfile
from backend.models.repository import Repository, MigrationJob
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("📦 Creating all tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ All tables created successfully!")
        logger.info("   - users")
        logger.info("   - user_profiles")
        logger.info("   - repositories")
        logger.info("   - migration_jobs")
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")

if __name__ == "__main__":
    main()