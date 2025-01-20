import pytest
import json
from linkml_toolkit.export import SchemaExporter


def test_export_json_schema(basic_schema, tmp_path):
    exporter = SchemaExporter(basic_schema)
    output_path = tmp_path / "schema.json"
    exporter.to_json_schema(output_path)

    with open(output_path) as f:
        json_schema = json.load(f)
    assert "$schema" in json_schema
    assert "definitions" in json_schema


def test_export_rdf(basic_schema, tmp_path):
    exporter = SchemaExporter(basic_schema)
    output_path = tmp_path / "schema.ttl"
    exporter.to_rdf(output_path, format="turtle")
    assert output_path.exists()


def test_export_graphql(basic_schema, tmp_path):
    exporter = SchemaExporter(basic_schema)
    output_path = tmp_path / "schema.graphql"
    exporter.to_graphql(output_path)
    assert output_path.exists()
