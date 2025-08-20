#!/bin/bash
# Environment Setup Helper Script
# This script helps set up the environment configuration for the Energy Prediction API

set -e

echo "Energy Prediction API - Environment Setup"
echo "============================================="
echo

# Check if .env already exists
if [ -f ".env" ]; then
    echo ".env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [[ ! $overwrite =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
fi

# Function to generate a random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to generate API key
generate_api_key() {
    openssl rand -hex 32
}

echo "Setting up environment configuration..."
echo

# Ask for environment type
echo "Select environment type:"
echo "1) Docker Compose (recommended for quick start)"
echo "2) Local Development (requires local PostgreSQL)"
echo "3) Production"
read -p "Choose option (1-3): " env_type

case $env_type in
    1)
        echo "Setting up for Docker Compose..."
        template=".env.example"
        db_host="db"
        ;;
    2)
        echo "Setting up for Local Development..."
        template=".env.dev"
        db_host="localhost"
        ;;
    3)
        echo "Setting up for Production..."
        template=".env.prod.example"
        db_host="your-db-host"
        ;;
    *)
        echo "Invalid option. Using Docker Compose setup."
        template=".env.example"
        db_host="db"
        ;;
esac

# Copy template
cp "$template" .env

# Generate secure password
password=$(generate_password)
echo "Generated secure database password: $password"

# Update database password in .env
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/password/$password/g" .env
else
    # Linux
    sed -i "s/password/$password/g" .env
fi

# Ask about API key
echo
read -p "Do you want to enable API key authentication? (y/N): " enable_api
if [[ $enable_api =~ ^[Yy]$ ]]; then
    api_key=$(generate_api_key)
    echo "Generated API key: $api_key"
    
    # Update API key in .env
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/API_KEY=/API_KEY=$api_key/" .env
    else
        sed -i "s/API_KEY=/API_KEY=$api_key/" .env
    fi
else
    echo "API key authentication will be disabled."
fi

echo
echo "Environment configuration complete!"
echo
echo "Configuration saved to .env"
echo

# Show next steps
case $env_type in
    1)
        echo "Next steps for Docker Compose:"
        echo "   docker-compose up --build"
        ;;
    2)
        echo "Next steps for Local Development:"
        echo "   1. Make sure PostgreSQL is running on localhost"
        echo "   2. Create the database: createdb energy_poc"
        echo "   3. Run: python migrations/create_db.py"
        echo "   4. Start API: uvicorn src.app:app --reload"
        ;;
    3)
        echo "Next steps for Production:"
        echo "   1. Review and update .env with your production values"
        echo "   2. Update DATABASE_URL with your production database"
        echo "   3. Deploy using your preferred method"
        ;;
esac

echo
echo "You can validate your configuration with:"
echo "   python scripts/validate_env.py"
echo
echo "For detailed configuration guide, see ENVIRONMENT.md"
