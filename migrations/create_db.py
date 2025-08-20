#!/usr/bin/env python3
"""
Database initialization script.
Creates all tables and optionally seeds with test data.
"""

import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from src.models import Base
from src.settings import settings

# Add the app directory and src to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(app_dir / "src"))


def create_database() -> None:
    """Create the database and all tables."""
    print(f"Connecting to database: {settings.database_url}")

    try:
        # Create engine
        engine = create_engine(settings.database_url, echo=True)

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"Connected to PostgreSQL: {version}")

        # Create all tables
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("All tables created successfully!")

    except OperationalError as e:
        print(f"Failed to connect to database: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is running")
        print("2. Database URL is correct")
        print("3. Database exists and user has permissions")
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_database()
