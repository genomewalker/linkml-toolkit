# Getting Started

LinkML Toolkit provides a command-line interface for working with LinkML schemas. All functionality is accessed through the `lmtk` command.

## Basic Usage

### Checking a Schema

Get a quick overview of a schema:
```bash
lmtk summary --schema schema.yaml
```

### Validating a Schema

Check if a schema is valid:
```bash
lmtk validate --schema schema.yaml
```

### Quiet Mode

All commands support quiet mode for suppressing non-error output:
```bash
lmtk -q validate --schema schema.yaml
```