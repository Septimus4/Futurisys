#!/usr/bin/env python3
"""
Database initialization script.
Creates database and all tables and optionally seeds with test data.
"""

import sys
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

# Add the app directory and src to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(app_dir / "src"))

from src.models import Base
from src.settings import settings


def create_database_if_not_exists() -> None:
    """Create the database if it doesn't exist."""
    # Parse the database URL to get connection details
    parsed_url = urlparse(settings.database_url)
    db_name = parsed_url.path[1:]  # Remove leading '/'
    
    # Create connection URL without database name for initial connection
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/postgres"
    
    print(f"Checking if database '{db_name}' exists...")
    
    try:
        # Connect to postgres database to check if target database exists
        engine = create_engine(base_url, echo=False, isolation_level="AUTOCOMMIT")
        
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            
            if result.fetchone() is None:
                print(f"Database '{db_name}' does not exist. Creating...")
                # Create the database (autocommit mode allows this)
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Database '{db_name}' created successfully!")
            else:
                print(f"Database '{db_name}' already exists.")
                
    except OperationalError as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is running")
        print("2. Connection details are correct")
        print("3. User has permissions to connect and create databases")
        sys.exit(1)


def create_tables() -> None:
    """Create all tables in the database."""
    print(f"Connecting to database: {settings.database_url}")

    try:
        # Create engine for the target database
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
    create_database_if_not_exists()
    create_tables()
