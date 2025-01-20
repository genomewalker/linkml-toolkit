# LinkML Toolkit (lmtk)

[![Tests](https://github.com/yourusername/linkml-toolkit/workflows/Tests/badge.svg)](https://github.com/yourusername/linkml-toolkit/actions)
[![PyPI version](https://badge.fury.io/py/linkml-toolkit.svg)](https://badge.fury.io/py/linkml-toolkit)
[![Documentation Status](https://readthedocs.org/projects/linkml-toolkit/badge/?version=latest)](https://linkml-toolkit.readthedocs.io/en/latest/?badge=latest)

A comprehensive toolkit for working with LinkML schemas. Provides functionality for analyzing, validating, merging, and converting LinkML schemas.

## Features

- 📊 Schema summarization with detailed views
- ✅ Schema validation with detailed error reporting
- 🔄 Merging multiple schemas with conflict resolution
- 📚 Concatenating schemas with namespace preservation
- 🔄 Export to various formats (JSON Schema, RDF, GraphQL)
- 📈 Progress tracking and rich console output
- 🛠️ Comprehensive CLI interface

## Installation

```bash
pip install linkml-toolkit
```

## Quick Start

```bash
# Get a summary of a schema
lmtk summary --schema schema.yaml

# Get detailed information about slots
lmtk summary --schema schema.yaml --section slots --detailed

# Validate a schema
lmtk validate --schema schema.yaml

# Merge multiple schemas
lmtk merge --schemas schema1.yaml,schema2.yaml --output merged.yaml

# Concatenate schemas
lmtk concat --schemas schema1.yaml,schema2.yaml --output combined.yaml

# Export to different formats
lmtk export --schema schema.yaml --format json --output schema.json
lmtk export --schema schema.yaml --format rdf --output schema.ttl
```

## Advanced Usage

### Working with Multiple Schemas

You can specify multiple schemas either by comma-separated list or through a file:

```bash
# Comma-separated list
lmtk merge --schemas schema1.yaml,schema2.yaml --output merged.yaml

# File containing paths
lmtk merge --schemas schema_list.txt --input-type file --output merged.yaml
```

### Detailed Schema Analysis

Get comprehensive information about schema components:

```bash
# Detailed view of all slots
lmtk summary --schema schema.yaml --section slots --detailed

# Export summary to JSON
lmtk summary --schema schema.yaml --detailed --output summary.json
```

### Schema Export

Export your schema to various formats:

```bash
# Export to all supported formats
lmtk export --schema schema.yaml --format all --output schema

# This will create:
# - schema.json (JSON Schema)
# - schema.ttl (RDF/Turtle)
# - schema.graphql (GraphQL)
```

## Documentation

Full documentation is available at [https://linkml-toolkit.readthedocs.io/](https://linkml-toolkit.readthedocs.io/)

## Development

Clone and install for development:

```bash
git clone https://github.com/yourusername/linkml-toolkit.git
cd linkml-toolkit
pip install -e ".[dev,docs]"
```

Run tests:
```bash
pytest
```

Build documentation:
```bash
cd docs
mkdocs build
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. See our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.