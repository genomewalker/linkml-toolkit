import pytest
from pathlib import Path
from linkml_toolkit.core import LinkMLProcessor


def test_load_schema(basic_schema):
    """Test basic schema loading."""
    processor = LinkMLProcessor(basic_schema)

    # Check basic schema properties
    assert processor.schema is not None
    assert processor.schema.name is not None
    assert processor.schema_view is not None
    assert len(processor.schema_view.all_classes()) > 0, "No classes found in schema"


def test_analyze_schema_basic(basic_schema):
    """Test basic schema analysis."""
    processor = LinkMLProcessor(basic_schema)

    # Basic analysis
    summary = processor.analyze_schema()

    # Print summary for debugging
    print("Schema Summary:", summary)

    assert "classes" in summary
    assert "slots" in summary
    assert "name" in summary

    # More flexible class checking
    assert len(summary.get("classes", {})) > 0, "No classes found in schema summary"

    # Specific class check
    assert any(
        "Person" in cls for cls in summary.get("classes", {})
    ), "Person class not found in schema summary"


def test_analyze_schema_detailed(basic_schema):
    """Test detailed schema analysis."""
    processor = LinkMLProcessor(basic_schema)

    # Detailed analysis
    detailed_summary = processor.analyze_schema(detailed=True)

    # Print detailed summary for debugging
    print("Detailed Schema Summary:", detailed_summary)

    assert "classes" in detailed_summary

    # More flexible class checking
    assert len(detailed_summary.get("classes", {})) > 0, "No classes found in detailed summary"

    # Specific class check
    assert any(
        "Person" in cls for cls in detailed_summary.get("classes", {})
    ), "Person class not found in detailed schema summary"


def test_analyze_specific_elements(basic_schema):
    """Test analyzing specific schema elements."""
    processor = LinkMLProcessor(basic_schema)

    # Analyze a specific class
    person_class = processor.analyze_class("Person")
    assert person_class is not None, "Could not find Person class"

    assert "slots" in person_class, "No slots found in Person class"

    # Analyze a specific slot
    name_slot = processor.analyze_slot("name")
    assert name_slot is not None, "Could not find 'name' slot"

    # Additional checks for slot
    assert "usage" in name_slot, "No usage information for slot"


def test_analyze_schema_sections(basic_schema):
    """Test analyzing specific schema sections."""
    processor = LinkMLProcessor(basic_schema)

    # Specific section analysis
    classes_only = processor.analyze_schema(sections=["classes"])
    assert "classes" in classes_only
    assert "slots" not in classes_only

    slots_only = processor.analyze_schema(sections=["slots"])
    assert "slots" in slots_only
    assert "classes" not in slots_only


def test_subset_schema(basic_schema):
    """Test creating a schema subset."""
    processor = LinkMLProcessor(basic_schema)

    # Create subset with specific class
    subset = processor.subset_schema(["Person"])
    assert "classes" in subset
    assert "Person" in subset["classes"]

    # Create subset with inherited properties
    subset_inherited = processor.subset_schema(["Person"], include_inherited=True)
    assert "classes" in subset_inherited
    assert "Person" in subset_inherited["classes"]


def test_generate_class_hierarchy(basic_schema):
    """Test generating class hierarchy text."""
    processor = LinkMLProcessor(basic_schema)

    # Generate hierarchy
    hierarchy_text = processor.generate_class_hierarchy_text()

    # Print hierarchy for debugging
    print("Class Hierarchy:\n", hierarchy_text)

    # Basic checks
    assert isinstance(hierarchy_text, str), "Hierarchy should be a string"
    assert len(hierarchy_text.strip()) > 0, "Hierarchy text should not be empty"
