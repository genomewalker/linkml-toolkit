import os
from click.testing import CliRunner
from pathlib import Path
import traceback
from linkml_toolkit.cli import main


def test_validate_command(basic_schema, invalid_schema):
    """Test CLI validation commands."""
    runner = CliRunner()

    # Validate good schema
    result = runner.invoke(main, ["validate", "--schema", str(basic_schema)])

    # Print detailed output for debugging
    print("\nValidation result for good schema:", result.output)

    # More flexible success check
    assert result.exit_code == 0, f"Validation of good schema failed: {result.output}"

    # More flexible output check
    assert any(
        keyword in result.output.lower() for keyword in ["passed", "validation", "success"]
    ), f"Unexpected validation output: {result.output}"

    # Validate invalid schema
    result = runner.invoke(main, ["validate", "--schema", str(invalid_schema)])

    # Print detailed output for debugging
    print("\nValidation result for invalid schema:", result.output)

    # More flexible checks
    assert any(
        [
            result.exit_code != 0,
            "warning" in result.output.lower(),
            "error" in result.output.lower(),
        ]
    ), f"Invalid schema should trigger an error or show warnings. Output: {result.output}"


def test_export_commands(basic_schema, tmp_path):
    """Test CLI export commands."""
    runner = CliRunner()

    # Ensure fully qualified paths for each format
    test_formats = {
        "json": "schema.json",
        "rdf": "schema.ttl",
        "graphql": "schema.graphql",
        "csv": "csvexport",  # CSV export creates a directory
    }

    for fmt, output_name in test_formats.items():
        if fmt == "csv":
            # Define output directory for CSV
            output_dir = tmp_path / output_name
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Define output file for other formats
            output_file = tmp_path / output_name

        # Invoke export command
        result = runner.invoke(
            main,
            [
                "export",
                "--schema",
                str(basic_schema),
                "--format",
                fmt,
                "--output",
                str(output_dir if fmt == "csv" else output_file),
            ],
        )

        # Print detailed error for debugging
        if result.exit_code != 0:
            print(f"\nExport to {fmt} failed with output: {result.output}")

        # Check CLI success
        assert result.exit_code == 0, f"Export to {fmt} failed: {result.output}"

        if fmt == "csv":
            # Check multiple CSV files for CSV export
            expected_files = ["classes.csv", "slots.csv", "types.csv", "enums.csv"]
            for filename in expected_files:
                file_path = output_dir / filename
                assert file_path.exists(), f"CSV file {filename} not created"
                with open(file_path, "r") as f:
                    content = f.read().strip()
                    assert len(content) > 0, f"CSV file {filename} is empty"
        else:
            # Verify output file creation
            assert output_file.exists(), f"File {output_name} not created"


def test_merge_command(basic_schema, second_schema, tmp_path):
    """Test CLI merge commands."""
    runner = CliRunner()

    # Merge schemas
    output_path = tmp_path / "merged.yaml"
    result = runner.invoke(
        main,
        [
            "combine",
            "--schema",
            str(basic_schema),
            "--additional-schemas",
            str(second_schema),
            "--output",
            str(output_path),
            "--mode",
            "merge",
        ],
    )

    # Print detailed output for debugging
    if result.exit_code != 0:
        print(f"\nMerge failed with output: {result.output}")

    # More flexible success check
    assert result.exit_code == 0, f"Schema merge failed: {result.output}"

    # Validate merge output
    assert output_path.exists(), "Merged schema file not created"

    # Read and check merged content
    with open(output_path, "r") as f:
        merged_content = f.read()

    # Flexible checks for merged content
    assert any(
        cls in merged_content for cls in ["Person", "Address"]
    ), "Merged schema missing expected classes"
