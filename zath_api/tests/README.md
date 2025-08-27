# ZATH API Tests

This directory contains all tests for the ZATH API.

## Test Structure

```
tests/
├── __init__.py              # Makes tests a Python package
├── conftest.py              # Pytest configuration and shared fixtures
├── test_authentication.py   # Legacy authentication test suite
├── test_authentication_pytest.py  # Pytest-style authentication tests
└── README.md               # This file
```

## Running Tests

### Option 1: Using pytest (Recommended)
```bash
# Run all tests
pytest

# Run only integration tests
pytest -m integration

# Run only unit tests
pytest -m unit

# Run specific test file
pytest tests/test_authentication_pytest.py

# Run with verbose output
pytest -v
```

### Option 2: Using test runner script
```bash
# Run pytest tests (default)
python run_tests.py

# Run legacy test suite
python run_tests.py --legacy

# Show help
python run_tests.py --help
```

### Option 3: Direct execution
```bash
# Run legacy test suite directly
python tests/test_authentication.py

# Run pytest directly
python -m pytest tests/
```

## Test Categories

### Integration Tests (`@pytest.mark.integration`)
- Test full API endpoints
- Require running server and database
- Test complete authentication flow

### Unit Tests (`@pytest.mark.unit`)
- Test individual functions and utilities
- Don't require external services
- Fast execution

## Adding New Tests

1. Create new test file following naming convention: `test_*.py`
2. Use appropriate pytest markers (`@pytest.mark.integration` or `@pytest.mark.unit`)
3. Use fixtures from `conftest.py` for common setup
4. Follow the existing test patterns

## Test Configuration

- `pytest.ini`: Pytest configuration
- `conftest.py`: Shared fixtures and test setup
- Environment variables are automatically set for testing

## Prerequisites

- Server must be running on `http://localhost:8000`
- Database must be accessible with test credentials
- All test dependencies installed (`pytest`, `pytest-asyncio`, `aiohttp`)
