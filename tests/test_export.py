import json
import csv
import pytest
import traceback
from pathlib import Path
from linkml_toolkit.export import SchemaExporter


def test_export_json_schema(basic_schema, tmp_path):
    """Test export to JSON Schema."""
    output_path = tmp_path / "schema.json"

    try:
        # Import here to handle potential import errors
        exporter = SchemaExporter(basic_schema)

        # Export to JSON Schema
        exporter.to_json_schema(output_path)

        # Verify file creation and content
        assert output_path.exists()

        # Safely load and check JSON
        with open(output_path) as f:
            json_schema = json.load(f)

        # Basic JSON Schema checks
        assert "$schema" in json_schema
        assert "$defs" in json_schema

        # Print full JSON schema for debugging if no Person definition
        if not any("Person" in str(key).lower() for key in json_schema.get("$defs", {})):
            print("\nFull JSON Schema:", json.dumps(json_schema, indent=2))

        # Flexible check for Person definition
        assert any(
            "person" in str(key).lower() for key in json_schema.get("$defs", {})
        ), "No Person-related definition found in JSON Schema"

    except Exception as e:
        # Print detailed error information
        print(f"\nJSON Schema export failed: {e}")
        print(f"Output path: {output_path}")
        print("\nFull traceback:")
        traceback.print_exc()
        raise


def test_checklist_template(tmp_path):
    """Test that slot titles are exported ordered by rank, not declaration order."""
    schema_path = tmp_path / "checklist_schema.yaml"
    schema_path.write_text(
        """
id: https://example.org/checklist_schema
name: checklist_schema
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
default_range: string

classes:
  Sample:
    slots:
      - sample_id
      - collection_date
      - host_taxon
    slot_usage:
      sample_id:
        rank: 3
      collection_date:
        rank: 1
      host_taxon:
        rank: 2

slots:
  sample_id:
    title: sample identifier
  collection_date:
    title: collection date
  host_taxon:
    title: host taxon
"""
    )
    output_path = tmp_path / "template.tsv"

    exporter = SchemaExporter(schema_path)
    exporter.to_checklist_template("Sample", output_path)

    with open(output_path, newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))

    assert rows == [["collection date", "host taxon", "sample identifier"]]


def test_checklist_template_repository_prefix(tmp_path):
    """Test that --repository ena prepends ENA's required columns."""
    schema_path = tmp_path / "checklist_schema.yaml"
    schema_path.write_text(
        """
id: https://example.org/checklist_schema
name: checklist_schema
prefixes:
  linkml: https://w3id.org/linkml/
imports:
  - linkml:types
default_range: string

classes:
  Sample:
    slots:
      - sample_id
    slot_usage:
      sample_id:
        rank: 1

slots:
  sample_id:
    title: sample identifier
"""
    )
    output_path = tmp_path / "template.tsv"

    exporter = SchemaExporter(schema_path)
    exporter.to_checklist_template("Sample", output_path, repository="ena")

    with open(output_path, newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))

    assert rows == [
        [
            "tax_id",
            "scientific_name",
            "sample_alias",
            "geographic location (latitude)",
            "geographic location (longitude)",
            "geographic location (country and/or sea)",
            "sample_title",
            "sample_description",
            "sample identifier",
        ]
    ]

    with pytest.raises(ValueError, match="Unsupported repository"):
        exporter.to_checklist_template("Sample", output_path, repository="sra")


def test_export_rdf(basic_schema, tmp_path):
    """Test export to RDF."""
    output_path = tmp_path / "schema.ttl"

    try:
        exporter = SchemaExporter(basic_schema)
        exporter.to_rdf(output_path, format="turtle")

        # Verify file creation and content
        assert output_path.exists(), f"RDF output file not created at {output_path}"

        with open(output_path) as f:
            content = f.read()

        # Basic RDF checks
        assert "@prefix" in content, "No RDF prefix found in output"

        # More flexible checks for RDF definitions
        assert any(
            keyword.lower() in content.lower()
            for keyword in ["owl:ontology", "rdf:type", "owl:class", "owl:property"]
        ), "No standard RDF class or property definitions found"

    except Exception as e:
        # Print detailed error information
        print(f"\nRDF export failed: {e}")
        print(f"Output path: {output_path}")
        print("\nFull traceback:")
        traceback.print_exc()
        raise
