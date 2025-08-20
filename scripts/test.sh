#!/bin/bash
# Local test runner script that matches CI behavior.
#
# Usage:
#     ./scripts/test.sh [options]
#
# Options:
#     --fast     Skip integration tests and coverage
#     --coverage Generate HTML coverage report
#     --lint     Run linting and formatting only

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
FAST=false
COVERAGE=false
LINT_ONLY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fast)
            FAST=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --lint)
            LINT_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}Running Energy Prediction API Tests${NC}"
echo "========================================"

# Check if model exists
if [ ! -f "model/energy_rf.joblib" ]; then
    echo -e "${RED}❌ Pre-trained model not found at model/energy_rf.joblib${NC}"
    echo "Please ensure the model exists before running tests."
    exit 1
fi

# Linting and formatting
echo -e "${YELLOW}🔍 Linting and Code Quality${NC}"
echo "ruff check src tests"
ruff check src tests

echo "ruff format --check src tests"
ruff format --check src tests

if [ "$LINT_ONLY" = true ]; then
    echo -e "${GREEN}✅ Linting completed successfully${NC}"
    exit 0
fi

# Unit and validation tests
echo -e "${YELLOW}🧪 Running Unit Tests${NC}"
if [ "$COVERAGE" = true ] || [ "$FAST" = false ]; then
    echo "python -m pytest tests/test_health.py tests/test_predict_ok.py tests/test_predict_validation.py --cov=src --cov-report=term-missing --cov-report=html -v"
    python -m pytest tests/test_health.py tests/test_predict_ok.py tests/test_predict_validation.py \
        --cov=src --cov-report=term-missing --cov-report=html -v
else
    echo "python -m pytest tests/test_health.py tests/test_predict_ok.py tests/test_predict_validation.py -v"
    python -m pytest tests/test_health.py tests/test_predict_ok.py tests/test_predict_validation.py -v
fi

# Integration tests (unless --fast)
if [ "$FAST" = false ]; then
    echo -e "${YELLOW}🔗 Running Integration Tests${NC}"
    echo "python -m pytest tests/test_integration.py -v"
    python -m pytest tests/test_integration.py -v
fi

# Demo script validation
echo -e "${YELLOW}Validating Demo Script${NC}"
echo "python -c 'from demo import EnergyAPIDemo; print(\"Demo imports successfully\")'"
python -c "from demo import EnergyAPIDemo; print('Demo imports successfully')"

echo -e "${GREEN}✅ All tests completed successfully!${NC}"

if [ "$COVERAGE" = true ]; then
    echo -e "${BLUE}📊 Coverage report generated in htmlcov/index.html${NC}"
fi

# Summary
echo ""
echo "Test Summary:"
echo "- Linting: ✅ Passed"
echo "- Code formatting: ✅ Passed"
echo "- Unit tests: ✅ Passed"
if [ "$FAST" = false ]; then
    echo "- Integration tests: ✅ Passed"
fi
echo "- Demo validation: ✅ Passed"

echo ""
echo "Next steps:"
echo "- Run 'python demo.py' to test the live API"
echo "- Use 'docker-compose up' to start the full stack"
if [ "$COVERAGE" = true ]; then
    echo "- Open htmlcov/index.html to view detailed coverage"
fi
