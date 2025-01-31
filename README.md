# LinkML Toolkit (lmtk)

[![Tests](https://github.com/genomewalker/linkml-toolkit/workflows/Tests/badge.svg)](https://github.com/genomewalker/linkml-toolkit/actions)
[![PyPI version](https://badge.fury.io/py/linkml-toolkit.svg)](https://badge.fury.io/py/linkml-toolkit)
[![Documentation Status](https://readthedocs.org/projects/linkml-toolkit/badge/?version=latest)](https://linkml-toolkit.readthedocs.io/en/latest/?badge=latest)

A simple toolkit for working with LinkML schemas. This tool offers advanced schema analysis, validation, transformation, and visualization capabilities through a flexible command-line interface.

## 🌟 Features

- **Schema Analysis**
  - Generate schema summaries.
  - Detailed views of classes, slots, and types.
  - Support for hierarchical and section-based analysis.

- **Schema Validation**
  - Rigorous validation checks with detailed error reporting.
  - Optional metadata display for schemas.

- **Schema Operations**
  - Merge or concatenate multiple schemas.
  - Subset schemas by specified classes.

- **Format Conversion**
  - Export schemas to JSON, RDF, GraphQL, CSV, TSV, and SQL formats.
  - Customize RDF serialization formats (e.g., Turtle, XML).
  - SQL export supporting PostgreSQL, MySQL, SQLite, and DuckDB dialects.

- **Visualization**
  - Generate interactive HTML visualizations of schemas.
  - Options for inheritance, descriptions, and statistics display.

## 🚀 Installation

### Using pip

```bash
pip install linkml-toolkit
```

### Using conda

```bash
# Create environment from provided configuration
conda env create -f environment-dev.yml
conda activate linkml-toolkit-dev

# For production environment only
conda env create -f environment.yml
conda activate linkml-toolkit
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/genomewalker/linkml-toolkit.git
cd linkml-toolkit

# Create and activate conda environment
conda env create -f environment-dev.yml
conda activate linkml-toolkit-dev

# Install in development mode
pip install -e ".[dev,test,docs]"
```

## 📚 Usage

### Core Commands

#### Schema Summary
```bash
# Generate a summary of the schema
lmtk summary --schema schema.yaml

# Detailed view for specific sections
lmtk summary --schema schema.yaml --section slots --detailed

# Export summary to JSON
lmtk summary --schema schema.yaml --output summary.json
```

#### Schema Validation
```bash
# Validate schema
lmtk validate --schema schema.yaml

# Validate with metadata display
lmtk validate --schema schema.yaml --metadata
```

#### Schema Export
```bash
# Export to JSON Schema
lmtk export --schema schema.yaml --format json --output schema.json

# Export to RDF (Turtle format)
lmtk export --schema schema.yaml --format rdf --rdf-format turtle --output schema.ttl

# Export to SQL (PostgreSQL dialect)
lmtk export --schema schema.yaml --format sql --sql-dialect postgresql --output schema.sql
```

#### Schema Subset
```bash
# Create a subset containing specific classes
lmtk subset --schema schema.yaml --classes class1,class2 --output subset.yaml

# Exclude inherited elements
lmtk subset --schema schema.yaml --classes class1 --no-inherited --output subset.yaml
```

#### Schema Combination
```bash
# Merge schemas
lmtk combine --schema base.yaml --additional-schemas schema1.yaml -a schema2.yaml --mode merge --output merged.yaml

# Concatenate schemas
lmtk combine --schema base.yaml --additional-schemas schema1.yaml -a schema2.yaml --mode concat --output concatenated.yaml
```

#### Schema Visualization
```bash
# Generate an interactive HTML visualization
lmtk visualize --schema schema.yaml --output visualization.html

# Generate full documentation bundle
lmtk visualize --schema schema.yaml --output docs/ --full-docs
```

## 🛠️ Development

### Environment Management

```bash
# Create development environment
conda env create -f environment.yml

# Update environment
conda env update -f environment.yml

# Create production environment
conda env create -f environment.prod.yml
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=linkml_toolkit

# Run specific test file
pytest tests/test_core.py

# Run tests with output
pytest -v
```

### Building Documentation

```bash
# Build documentation
cd docs
mkdocs build

# Serve documentation locally
mkdocs serve
```

## 📖 Project Structure

```
linkml-toolkit/
├── src/
│   └── linkml_toolkit/      # Source code
├── tests/                   # Test suite
│   └── data/               # Test data
├── docs/                    # Documentation
├── environment.yml         # Development environment
├── environment.prod.yml    # Production environment
├── pyproject.toml         # Build configuration
├── setup.cfg              # Package metadata
└── tox.ini               # Test automation
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the Repository**
   ```bash
   git clone https://github.com/genomewalker/linkml-toolkit.git
   cd linkml-toolkit
   ```

2. **Set Up Development Environment**
   ```bash
   conda env create -f environment.yml
   conda activate linkml-toolkit
   pip install -e ".[dev,test,docs]"
   ```

3. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make Changes**
   - Write code
   - Add tests
   - Update documentation

5. **Verify Changes**
   ```bash
   # Run tests
   pytest
   
   # Run linting
   tox -e lint
   
   # Build docs
   cd docs && mkdocs build
   ```

6. **Submit Pull Request**
   - Push changes to your fork
   - Create pull request
   - Wait for review

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- LinkML community for the base LinkML implementation.
- Contributors who have helped improve this toolkit.

## 📫 Contact

- Issue Tracker: [GitHub Issues](https://github.com/genomewalker/linkml-toolkit/issues)
- Documentation: [ReadTheDocs](https://linkml-toolkit.readthedocs.io/)
