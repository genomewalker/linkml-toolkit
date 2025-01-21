import pytest
from linkml_toolkit.core import LinkMLProcessor


def test_merge_multiple(basic_schema, second_schema):
    """Test merging multiple schemas."""
    schema_list = f"{basic_schema},{second_schema}"

    # Merge schemas
    merged = LinkMLProcessor.merge_multiple(schema_list, return_errors=False)

    # Verify merged schema contents
    assert merged is not None
    assert "classes" in merged
    assert "Person" in merged["classes"]
    assert "Address" in merged["classes"]

    # Check metadata preservation
    assert "name" in merged
    assert "id" in merged


def test_concat_multiple(basic_schema, second_schema):
    """Test concatenating multiple schemas."""
    schema_list = f"{basic_schema},{second_schema}"

    # Concatenate schemas
    concatenated = LinkMLProcessor.concat_multiple(schema_list, return_errors=False)

    # Verify concatenated schema contents
    assert concatenated is not None
    assert "classes" in concatenated

    # Check that schemas are preserved with unique names
    assert "Person" in concatenated["classes"]
    assert any(name.startswith("Person") for name in concatenated["classes"])

    # Check schema has separate unique elements
    class_names = list(concatenated["classes"].keys())
    assert len(class_names) >= 2, "Concatenation should preserve classes from both schemas"
