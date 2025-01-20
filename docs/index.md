# LinkML Toolkit

A comprehensive toolkit for working with LinkML schemas. Provides functionality for analyzing, validating, merging, and converting LinkML schemas.

## Features

- 📊 Schema summarization with detailed views
- ✅ Schema validation with detailed error reporting
- 🔄 Merging multiple schemas with conflict resolution
- 📚 Concatenating schemas with namespace preservation
- 🔄 Export to various formats (JSON Schema, RDF, GraphQL)
- 📈 Progress tracking and rich console output
- 🛠️ Comprehensive CLI interface

## Quick Start

```bash
# Install the toolkit
pip install linkml-toolkit

# Get a summary of a schema
lmtk summary --schema schema.yaml

# Validate a schema
lmtk validate --schema schema.yaml

# Merge multiple schemas
lmtk merge --schemas schema1.yaml,schema2.yaml --output merged.yaml
```

# File: docs/installation.md
# Installation

## Prerequisites

LinkML Toolkit requires:
- Python 3.7 or later
- LinkML
- Click
- Rich

## Installation Methods

### From PyPI

```bash
pip install linkml-toolkit
```

### From Source

```bash
git clone https://github.com/yourusername/linkml-toolkit.git
cd linkml-toolkit
pip install -e .
```

### Development Installation

For development, install with additional dependencies:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install with documentation dependencies
pip install -e ".[docs]"

# Install with test dependencies
pip install -e ".[test]"
```