import pytest
from linkml_toolkit.validation import SchemaValidator, display_validation_errors
import traceback


def test_validate_valid_schema(basic_schema):
    """Test validation of a valid schema."""
    validator = SchemaValidator()
    errors = validator.validate_schema(basic_schema)

    # Log errors for debugging
    if errors:
        print("Unexpected errors:", [e.message for e in errors])

    # Allow only warning-level issues
    assert all(
        e.severity == "WARNING" or e.message.startswith("Schema validation passed") for e in errors
    ), f"Validation should only allow warnings. Found: {errors}"


def test_validate_invalid_schema(invalid_schema):
    """Test validation of an invalid schema."""
    validator = SchemaValidator()
    errors = validator.validate_schema(invalid_schema)

    # Log errors for debugging
    print("Validation Errors:", [e.message for e in errors])

    # Ensure some validation errors or warnings exist
    assert len(errors) > 0, "Invalid schema should have validation errors or warnings"

    # More flexible error checking
    error_messages = [str(e.message).lower() for e in errors]
    error_severities = [e.severity for e in errors]

    # Checks for validation issues
    checks = [
        any("missing" in msg or "required" in msg for msg in error_messages),
        any("id" in msg or "identifier" in msg for msg in error_messages),
        any(severity == "WARNING" for severity in error_severities),
    ]

    # Require at least one check to pass
    assert any(checks), f"Invalid schema validation failed. Errors: {error_messages}"


def test_validate_multiple_schemas(basic_schema, second_schema, invalid_schema):
    """Test multiple schema validation."""
    validator = SchemaValidator()

    # Validate multiple schemas
    results = validator.validate_multiple([basic_schema, second_schema, invalid_schema])

    # Check results for each schema
    assert len(results) == 3, "Should validate all provided schemas"

    # Basic and second schemas should only have warnings or no errors
    for schema_path in [basic_schema, second_schema]:
        schema_errors = results[str(schema_path)]
        assert all(
            e.severity == "WARNING" for e in schema_errors
        ), f"Basic schemas should only have warnings. Found: {schema_errors}"

    # Invalid schema should have validation issues
    invalid_errors = results[str(invalid_schema)]
    assert len(invalid_errors) > 0, "Invalid schema should have validation errors or warnings"


def test_display_validation_errors(basic_schema, invalid_schema):
    """Test the display_validation_errors function."""
    from linkml_toolkit.validation import display_validation_errors

    # Validate basic schema
    basic_errors = SchemaValidator().validate_schema(basic_schema)
    error_found = display_validation_errors(basic_errors)

    # Validate invalid schema
    invalid_errors = SchemaValidator().validate_schema(invalid_schema)
    error_found_invalid = display_validation_errors(invalid_errors)

    # Tests
    assert not error_found, "No errors should be found for a valid schema"
    assert error_found_invalid, "Errors should be found for an invalid schema"
