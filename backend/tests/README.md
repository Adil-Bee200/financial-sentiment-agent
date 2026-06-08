# Tests

This directory contains unit tests for the Financial Agent application.

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage report
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_llm_service.py
```

### Run specific test class
```bash
pytest tests/test_llm_service.py::TestRelevanceGate
```

### Run specific test
```bash
pytest tests/test_llm_service.py::TestRelevanceGate::test_relevance_relevant_article
```

### Run with verbose output
```bash
pytest -v
```

## Test Structure

- `conftest.py` - Pytest fixtures and configuration
- `test_llm_service.py` - Tests for LLM service (relevance, summarization, sentiment)

## Test Coverage

The tests use mocked OpenAI API calls to avoid making real API requests during testing. This ensures:
- Tests run fast
- No API costs
- Tests are deterministic
- Can test error scenarios

## Writing New Tests

1. Create test files with `test_*.py` naming
2. Use fixtures from `conftest.py` when possible
3. Mock external dependencies (APIs, databases, etc.)
4. Follow the existing test structure

## Coverage Reports

After running tests with coverage, view the HTML report:
```bash
# Generate HTML report
pytest --cov=app --cov-report=html

# Open the report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```
