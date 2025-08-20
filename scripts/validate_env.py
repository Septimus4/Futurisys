#!/usr/bin/env python3
"""
Environment Configuration Validator

This script validates that all required environment variables are properly set
and that the configuration is working correctly.
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists."""
    env_file = Path(".env")
    if not env_file.exists():
        print(".env file not found!")
        print("   Run: cp .env.example .env")
        return False
    print(".env file exists")
    return True

def validate_settings():
    """Validate settings can be loaded."""
    try:
        # Add current directory to Python path
        sys.path.insert(0, str(Path.cwd()))
        from src.settings import settings
        print("Settings loaded successfully")
        return settings
    except Exception as e:
        print(f"Failed to load settings: {e}")
        return None

def check_required_vars(settings):
    """Check required environment variables."""
    issues = []
    
    # Check database URL
    if not settings.database_url:
        issues.append("DATABASE_URL is not set")
    elif "password" in settings.database_url.lower() and "password@" in settings.database_url:
        issues.append("DATABASE_URL contains default password 'password' - change it!")
    else:
        print("DATABASE_URL is configured")
    
    # Check if using default postgres password
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    if postgres_password == "password":
        issues.append("POSTGRES_PASSWORD is set to default 'password' - change it!")
    elif postgres_password:
        print("POSTGRES_PASSWORD is configured")
    else:
        print("ℹPOSTGRES_PASSWORD not set (only needed for docker-compose)")
    
    return issues

def check_database_connection(settings):
    """Test database connection."""
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("Database connection successful")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("   Make sure your database is running and credentials are correct")
        return False

def check_model_files(settings):
    """Check if model files exist."""
    model_path = settings.get_model_artifact_path()
    card_path = settings.get_model_card_path()
    
    if model_path.exists():
        print("Model artifact found")
    else:
        print(f"Model artifact not found: {model_path}")
    
    if card_path.exists():
        print("Model card found")
    else:
        print(f"Model card not found: {card_path}")

def check_api_key(settings):
    """Check API key configuration."""
    if settings.is_api_key_enabled():
        if len(settings.api_key) < 16:
            print("API key is very short - consider using a longer key")
        else:
            print("API key is configured")
    else:
        print("API key authentication is disabled")

def main():
    """Main validation function."""
    print("🔍 Validating Environment Configuration\n")
    
    # Check if we're in the right directory
    if not Path("src").exists():
        print("Please run this script from the project root directory")
        sys.exit(1)
    
    success = True
    
    # Check .env file
    if not check_env_file():
        success = False
    
    print()
    
    # Load settings
    settings = validate_settings()
    if not settings:
        success = False
        sys.exit(1)
    
    print()
    
    # Check required variables
    issues = check_required_vars(settings)
    if issues:
        print("Configuration issues found:")
        for issue in issues:
            print(f"   - {issue}")
        success = False
    
    print()
    
    # Test database connection
    if not check_database_connection(settings):
        success = False
    
    print()
    
    # Check model files
    check_model_files(settings)
    
    print()
    
    # Check API key
    check_api_key(settings)
    
    print()
    
    if success:
        print("Configuration validation passed!")
        print("\nYou can now start the application:")
        print("   Docker: docker-compose up")
        print("   Local:  uvicorn src.app:app --reload")
    else:
        print("Configuration validation failed!")
        print("\nPlease fix the issues above before starting the application.")
        print("See ENVIRONMENT.md for detailed configuration guide.")
        sys.exit(1)

if __name__ == "__main__":
    main()
