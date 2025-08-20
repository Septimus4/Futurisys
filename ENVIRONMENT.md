# Environment Configuration Guide

This project uses environment variables for configuration to avoid hardcoded credentials and make deployment flexible.

## Quick Start

### Automated Setup (Recommended)

Run the interactive setup script:
```bash
./scripts/setup_env.sh
```

This script will:
- Guide you through environment type selection
- Generate secure passwords and API keys
- Create the appropriate .env file
- Provide next steps for your chosen environment

### Manual Setup

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file with your actual values:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Update sensitive values like passwords and API keys**

### Validation

After setup, validate your configuration:
```bash
python scripts/validate_env.py
```

This will check for:
- Required environment variables
- Database connectivity
- Security issues (default passwords, etc.)
- Model file availability

## Environment Files

- **`.env.example`** - Template with safe defaults, committed to git
- **`.env`** - Your actual environment configuration (NOT committed to git)
- **`.env.dev`** - Development-specific configuration template
- **`.env.prod.example`** - Production configuration template

## Required Variables

### Database Configuration
- `DATABASE_URL` - PostgreSQL connection string
  - Development: `postgresql+psycopg://user:password@localhost:5432/energy_poc`
  - Docker: `postgresql+psycopg://user:password@db:5432/energy_poc`
  - Production: `postgresql+psycopg://prod_user:secure_pass@prod_host:5432/energy_prod`

### PostgreSQL (for Docker Compose)
- `POSTGRES_DB` - Database name (default: energy_poc)
- `POSTGRES_USER` - Database user (default: user)
- `POSTGRES_PASSWORD` - Database password (**REQUIRED in production**)

## Optional Variables

### Security
- `API_KEY` - API key for authentication (leave empty to disable auth)

### Model Configuration
- `MODEL_ARTIFACT_PATH` - Path to model file (default: model/energy_rf.joblib)
- `MODEL_CARD_PATH` - Path to model metadata (default: model/model_card.json)
- `MODEL_NAME` - Model identifier (default: sklearn-random-forest)

### Application Settings
- `LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `DEBUG` - Enable debug mode: true/false (default: false)
- `MAX_SINGLE_REQUEST_SIZE_KB` - Max single request size (default: 16)
- `MAX_BATCH_REQUEST_SIZE_MB` - Max batch request size (default: 1)
- `MAX_BATCH_SIZE` - Max items in batch (default: 512)
- `INFERENCE_TIMEOUT_SECONDS` - Inference timeout (default: 5)

## Usage Examples

### Local Development
```bash
# Use development environment
cp .env.dev .env
# Edit DATABASE_URL if needed for your local PostgreSQL
```

### Docker Development
```bash
# Use the default .env file
cp .env.example .env
# The DATABASE_URL should point to 'db' hostname for docker-compose
```

### Production Deployment
```bash
# Create production environment
cp .env.prod.example .env.prod
# Edit with your production values
# Use .env.prod with your deployment system
```

### GitHub Actions CI/CD
The CI/CD pipeline uses GitHub repository variables:
- `TEST_DATABASE_URL` - Override for test database connection

Set these in your GitHub repository under Settings > Secrets and variables > Actions.

## Security Best Practices

1. **Never commit `.env` files** - They are in `.gitignore`
2. **Use strong passwords** - Especially for production databases
3. **Rotate API keys regularly** - Update them periodically
4. **Use different credentials for each environment** - Dev, staging, prod should be separate
5. **Limit database permissions** - Use principle of least privilege
6. **Enable API key authentication in production** - Set `API_KEY` environment variable

## Troubleshooting

### Common Issues

1. **Database connection fails:**
   - Check DATABASE_URL format
   - Verify database is running
   - Check network connectivity

2. **API key authentication not working:**
   - Ensure API_KEY is set in environment
   - Check X-API-Key header in requests
   - Verify API key matches exactly

3. **Docker compose fails:**
   - Check POSTGRES_PASSWORD is set
   - Verify .env file exists
   - Check Docker environment variable interpolation

### Validation

Test your configuration:
```bash
# Check environment loading
python -c "from src.settings import settings; print(settings.model_dump())"

# Test database connection
python migrations/create_db.py

# Test API with authentication
curl -H "X-API-Key: your-api-key" http://localhost:8000/health
```
