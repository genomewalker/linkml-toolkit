import pytest
from pathlib import Path
from linkml_toolkit.core import LinkMLProcessor


def test_load_schema(basic_schema):
    processor = LinkMLProcessor(basic_schema)
    assert processor.schema is not None
    assert processor.schema["name"] == "basic_schema"
    assert "classes" in processor.schema
    assert "Person" in processor.schema["classes"]


def test_get_summary_basic(basic_schema):
    processor = LinkMLProcessor(basic_schema)
    summary = processor.get_summary()
    assert "classes" in summary
    assert "slots" in summary
    assert "types" in summary
    assert len(summary["classes"]) == 1
    assert len(summary["slots"]) == 3
    assert len(summary["types"]) == 2


def test_get_summary_detailed(basic_schema):
    processor = LinkMLProcessor(basic_schema)
    summary = processor.get_summary(detailed=True)
    assert "classes" in summary
    person_details = summary["classes"]["Person"]
    assert "slots" in person_details
    assert len(person_details["slots"]) == 3


@pytest.mark.parametrize("section", ["classes", "slots", "types"])
def test_get_summary_sections(basic_schema, section):
    processor = LinkMLProcessor(basic_schema)
    summary = processor.get_summary(sections=[section])
    assert section in summary
    assert len(summary) == 1
