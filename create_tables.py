# create_tables.py
"""Script to create database tables"""

from backend.core.database import engine, Base
from backend.models.user import User, UserProfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tables created successfully!")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")

if __name__ == "__main__":
    main()