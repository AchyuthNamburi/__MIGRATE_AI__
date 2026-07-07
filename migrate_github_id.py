# migrate_github_id.py
"""Migrate github_id from Integer to BigInteger"""

from sqlalchemy import text
from backend.core.database import engine

def migrate():
    with engine.connect() as conn:
        # Drop the old table and recreate with BigInteger
        conn.execute(text("DROP TABLE IF EXISTS migration_jobs CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS repositories CASCADE;"))
        conn.commit()
        print("✅ Dropped old tables")
        
        # Recreate tables with BigInteger
        from backend.core.database import Base
        from backend.models.repository import Repository, MigrationJob
        Base.metadata.create_all(bind=engine)
        print("✅ Tables recreated with BigInteger")
        
if __name__ == "__main__":
    migrate()