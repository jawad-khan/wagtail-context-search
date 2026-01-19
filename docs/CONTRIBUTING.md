# Contributing to Wagtail Context Search

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/wagtail-context-search.git
   cd wagtail-context-search
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Setup

1. Install pre-commit hooks (optional but recommended):
   ```bash
   pre-commit install
   ```

2. Run tests to ensure everything works:
   ```bash
   pytest
   ```

## Making Changes

### Code Style

- Follow PEP 8
- Use Black for formatting (configured in the project)
- Maximum line length: 88 characters
- Use type hints where appropriate

### Commit Messages

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Example:
```
feat: Add support for Cohere LLM backend
```

### Pull Request Process

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make your changes and commit:
   ```bash
   git commit -m "feat: Add my feature"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/my-feature
   ```

4. Create a pull request on GitHub

5. Ensure all tests pass and code is properly formatted

## Adding New Backends

When adding a new backend (LLM, embedder, or vector DB):

1. Create the backend class following existing patterns
2. Add tests
3. Update documentation
4. Add to the appropriate registry
5. Update `requirements.txt` if new dependencies are needed

## Writing Tests

- Write tests for new features
- Aim for good coverage
- Use descriptive test names
- Mock external services/APIs

Example:
```python
def test_new_backend_initialization(self):
    backend = NewBackend(config)
    self.assertTrue(backend.is_available())
```

## Documentation

- Update relevant documentation when adding features
- Add examples for new functionality
- Keep documentation clear and concise

## Reporting Issues

When reporting bugs:

1. Check existing issues first
2. Provide a clear description
3. Include steps to reproduce
4. Include environment details (Python version, Django version, etc.)
5. Include error messages/logs

## Feature Requests

For feature requests:

1. Check if it's already requested
2. Provide a clear description
3. Explain the use case
4. Consider implementation complexity

## Code Review

All contributions go through code review. Be open to feedback and suggestions.

## Questions?

Feel free to open an issue for questions or discussions.

Thank you for contributing! 🎉
