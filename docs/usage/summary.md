# Schema Summary

The `summary` command provides an overview of a LinkML schema's contents.

## Basic Summary

Get a basic summary showing counts and names of schema components:
```bash
lmtk summary --schema schema.yaml
```

## Detailed Summary

Get detailed information about schema components:
```bash
lmtk summary --schema schema.yaml --detailed
```

## Filtering Sections

View specific sections of the schema:
```bash
# Show only slots
lmtk summary --schema schema.yaml --section slots

# Show multiple sections
lmtk summary --schema schema.yaml -s classes -s slots
```

# File: docs/usage/validation.md
# Schema Validation

The `validate` command performs simple validation of LinkML schemas.

## Basic Validation

```bash
lmtk validate --schema schema.yaml
```

Validation checks include:
- YAML syntax
- Required fields
- Reference integrity
- LinkML model compliance

## Error Reporting

Validation errors are reported with:
- Error location
- Error description
- Relevant context

# File: docs/usage/merge.md
# Merging Schemas

The `merge` command combines multiple schemas by updating/overwriting elements.

## Basic Usage

Merge using comma-separated list:
```bash
lmtk merge --schemas schema1.yaml,schema2.yaml --output merged.yaml
```

Using a file containing schema paths:
```bash
lmtk merge --schemas schema_list.txt --input-type file --output merged.yaml
```

## Behavior

- Later schemas override earlier ones
- All schema elements are combined
- Conflicts are resolved by last-wins

# File: docs/usage/concat.md
# Concatenating Schemas

The `concat` command combines schemas while preserving their namespaces.

## Basic Usage

```bash
lmtk concat --schemas schema1.yaml,schema2.yaml --output combined.yaml
```

## Behavior

- Maintains separate namespaces
- Renames conflicting elements with schema name suffix
- Preserves all elements from all schemas

# File: docs/usage/export.md
# Exporting Schemas

The `export` command converts LinkML schemas to other formats.

## Available Formats

- JSON Schema
- RDF (multiple serializations)
- GraphQL

## Usage

```bash
# Export to JSON Schema
lmtk export --schema schema.yaml --format json --output schema.json

# Export to RDF (Turtle format)
lmtk export --schema schema.yaml --format rdf --output schema.ttl

# Export to all formats
lmtk export --schema schema.yaml --format all --output schema
```