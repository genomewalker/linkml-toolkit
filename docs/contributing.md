# Contributing to LinkML Toolkit

We welcome contributions to the LinkML Toolkit! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/genomewalker/linkml-toolkit.git
   cd linkml-toolkit
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

4. Install development dependencies:
   ```bash
   pip install -e ".[dev,test,docs]"
   ```

## Running Tests

Run the test suite:
```bash
pytest
```

With coverage:
```bash
pytest --cov=linkml_toolkit
```

## Code Style

We use:
- Black for code formatting
- isort for import sorting
- mypy for type checking

Run linting:
```bash
tox -e lint
```

## Building Documentation

Build the documentation:
```bash
cd docs
mkdocs build
```

Serve documentation locally:
```bash
mkdocs serve
```

## Pull Request Process

1. Create a feature branch
2. Make your changes
3. Add tests for new functionality
4. Update documentation as needed
5. Run tests and linting
6. Submit PR