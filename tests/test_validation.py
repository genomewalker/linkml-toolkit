import pytest
from linkml_toolkit.validation import SchemaValidator


def test_validate_valid_schema(basic_schema):
    validator = SchemaValidator()
    errors = validator.validate_schema(basic_schema)
    assert not errors


def test_validate_invalid_schema(invalid_schema):
    validator = SchemaValidator()
    errors = validator.validate_schema(invalid_schema)
    assert errors
    assert len(errors) > 0
    error_messages = [e.message for e in errors]
    assert any("Missing required field: id" in msg for msg in error_messages)


def test_validate_multiple_schemas(basic_schema, second_schema, invalid_schema):
    validator = SchemaValidator()
    results = validator.validate_multiple([basic_schema, second_schema, invalid_schema])
    assert len(results) == 3
    assert not results[str(basic_schema)]  # No errors
    assert not results[str(second_schema)]  # No errors
    assert results[str(invalid_schema)]  # Has errors
