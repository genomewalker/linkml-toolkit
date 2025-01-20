from click.testing import CliRunner
from linkml_toolkit.cli import main


def test_summary_command(basic_schema):
    runner = CliRunner()
    result = runner.invoke(main, ["summary", "--schema", str(basic_schema)])
    assert result.exit_code == 0
    assert "Schema Summary" in result.output
    assert "Person" in result.output


def test_validate_command(basic_schema, invalid_schema):
    runner = CliRunner()
    # Test valid schema
    result = runner.invoke(main, ["validate", "--schema", str(basic_schema)])
    assert result.exit_code == 0
    assert "successful" in result.output

    # Test invalid schema
    result = runner.invoke(main, ["validate", "--schema", str(invalid_schema)])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_merge_command(basic_schema, second_schema, tmp_path):
    output_path = tmp_path / "merged.yaml"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["merge", "--schemas", f"{basic_schema},{second_schema}", "--output", str(output_path)],
    )
    assert result.exit_code == 0
    assert output_path.exists()


def test_quiet_mode(basic_schema):
    runner = CliRunner()
    result = runner.invoke(main, ["-q", "summary", "--schema", str(basic_schema)])
    assert result.exit_code == 0
    assert not result.output  # Should be empty in quiet mode
