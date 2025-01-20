import pytest
from pathlib import Path
from linkml_toolkit.core import LinkMLProcessor


def test_merge_schemas(basic_schema, second_schema, tmp_path):
    output_path = tmp_path / "merged.yaml"
    schema_list = f"{basic_schema},{second_schema}"

    merged = LinkMLProcessor.merge_multiple(schema_list)
    assert merged is not None
    assert "classes" in merged
    assert "Person" in merged["classes"]
    assert "Address" in merged["classes"]

    # Check that Person class has combined slots
    person_slots = merged["classes"]["Person"]["slots"]
    assert all(slot in person_slots for slot in ["id", "name", "age", "email"])


def test_concat_schemas(basic_schema, second_schema, tmp_path):
    output_path = tmp_path / "concatenated.yaml"
    schema_list = f"{basic_schema},{second_schema}"

    concatenated = LinkMLProcessor.concat_multiple(schema_list)
    assert concatenated is not None
    assert "classes" in concatenated

    # Check that Person class is renamed in second schema
    assert "Person" in concatenated["classes"]
    assert "Person_second_schema" in concatenated["classes"]


def test_schema_list_loading(basic_schema, second_schema, tmp_path):
    # Test comma-separated list
    schema_list = f"{basic_schema},{second_schema}"
    paths = LinkMLProcessor._load_schema_list(schema_list)
    assert len(paths) == 2

    # Test file list
    list_file = tmp_path / "schema_list.txt"
    with open(list_file, "w") as f:
        f.write(f"{basic_schema}\n{second_schema}")

    paths = LinkMLProcessor._load_schema_list(str(list_file), input_type="file")
    assert len(paths) == 2
