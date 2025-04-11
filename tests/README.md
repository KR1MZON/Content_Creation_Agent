# Testing the LinkedIn Post Automation API

This directory contains tests for the LinkedIn Post Automation API. The tests cover various components of the application, including content generation, API endpoints, and database models.

## Test Structure

- `test_content_generator.py`: Tests for the AI content generation functionality
- `test_content_api.py`: Tests for the content generation API endpoints
- `test_models.py`: Tests for the database models and relationships

## Running Tests

To run the tests, you'll need to have pytest installed. If you don't have it already, you can install it using pip:

```bash
pip install pytest pytest-asyncio
```

### Running All Tests

From the root directory of the project, run:

```bash
python -m pytest tests/
```

### Running Specific Test Files

To run tests from a specific file:

```bash
python -m pytest tests/test_content_generator.py
```

### Running Specific Test Functions

To run a specific test function:

```bash
python -m pytest tests/test_content_generator.py::test_content_generator_init
```

## Test Environment

The tests use:

- Mock objects to simulate external dependencies like OpenAI and Groq APIs
- In-memory SQLite database for testing database models
- FastAPI TestClient for testing API endpoints

## Adding New Tests

When adding new features to the application, make sure to add corresponding tests. Follow these guidelines:

1. **Unit Tests**: Test individual functions and methods in isolation
2. **Integration Tests**: Test how components work together
3. **API Tests**: Test API endpoints using the FastAPI TestClient
4. **Mock External Dependencies**: Use unittest.mock to mock external services

## Test Coverage

To check test coverage, install pytest-cov:

```bash
pip install pytest-cov
```

Then run:

```bash
python -m pytest --cov=app tests/
```

This will show you which parts of the code are covered by tests and which parts need more testing.

## Continuous Integration

Consider setting up a CI pipeline (e.g., GitHub Actions) to automatically run tests on every push or pull request to ensure code quality and prevent regressions.