"""Command line interface for the LinkML Toolkit."""

import click
from rich.console import Console
from rich.table import Table
from pathlib import Path
import logging
import sys
from typing import List, Optional

from .core import LinkMLProcessor
from .validation import SchemaValidator
from .export import SchemaExporter
from . import __version__

console = Console()


def setup_logging(quiet: bool):
    """Setup logging configuration."""
    level = logging.WARNING if quiet else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")


@click.group()
@click.option("--quiet", "-q", is_flag=True, help="Suppress all output except errors")
@click.version_option(version=__version__)
def main(quiet):
    """LinkML Toolkit (lmtk) - A comprehensive toolkit for working with LinkML schemas."""
    setup_logging(quiet)


@main.command()
@click.option(
    "--schema",
    type=click.Path(exists=True),
    required=True,
    help="Path to the LinkML schema file to validate",
)
def validate(schema):
    """Validate a LinkML schema file."""
    validator = SchemaValidator()
    errors = validator.validate_schema(schema)

    if errors:
        console.print(validator.format_errors(errors))
        sys.exit(1)
    else:
        console.print("[green]Schema validation successful![/green]")


@main.command()
@click.option(
    "--schema",
    type=click.Path(exists=True),
    required=True,
    help="Path to the LinkML schema file",
)
@click.option(
    "--section",
    "-s",
    multiple=True,
    type=click.Choice(["classes", "slots", "enums", "types"], case_sensitive=False),
    help="Sections to include in summary (can be specified multiple times)",
)
@click.option(
    "--detailed", "-d", is_flag=True, help="Show detailed information for each item"
)
@click.option("--no-validate", is_flag=True, help="Skip schema validation")
@click.option("--output", "-o", type=click.Path(), help="Save summary to a file")
def summary(schema, section, detailed, no_validate, output):
    """Display a summary of the LinkML schema."""
    try:
        processor = LinkMLProcessor(schema, validate=not no_validate)
        sections = list(section) if section else None
        summary_data = processor.get_summary(sections=sections, detailed=detailed)

        if output:
            import json

            with open(output, "w") as f:
                json.dump(summary_data, f, indent=2)
            console.print(f"Summary saved to: {output}")
            return

        schema_name = Path(schema).name
        display_summary(schema_name, summary_data, detailed)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@main.command()
@click.option(
    "--schemas",
    required=True,
    help="Comma-separated list of schema files or path to a file containing schema paths",
)
@click.option(
    "--input-type",
    type=click.Choice(["auto", "file", "list"]),
    default="auto",
    help="Specify how to interpret the schemas parameter",
)
@click.option(
    "--output",
    type=click.Path(),
    required=True,
    help="Path for the output merged schema file",
)
@click.option("--no-validate", is_flag=True, help="Skip schema validation")
def merge(schemas, input_type, output, no_validate):
    """Merge multiple LinkML schemas."""
    try:
        merged_schema = LinkMLProcessor.merge_multiple(
            schemas, input_type=input_type, validate=not no_validate
        )

        first_schema = LinkMLProcessor._load_schema_list(
            schemas, input_type=input_type
        )[0]
        processor = LinkMLProcessor(first_schema, validate=False)
        processor.save(merged_schema, output)
        console.print(f"[green]Successfully merged schemas to: {output}[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@main.command()
@click.option(
    "--schemas",
    required=True,
    help="Comma-separated list of schema files or path to a file containing schema paths",
)
@click.option(
    "--input-type",
    type=click.Choice(["auto", "file", "list"]),
    default="auto",
    help="Specify how to interpret the schemas parameter",
)
@click.option(
    "--output",
    type=click.Path(),
    required=True,
    help="Path for the output concatenated schema file",
)
@click.option("--no-validate", is_flag=True, help="Skip schema validation")
def concat(schemas, input_type, output, no_validate):
    """Concatenate multiple LinkML schemas."""
    try:
        concatenated_schema = LinkMLProcessor.concat_multiple(
            schemas, input_type=input_type, validate=not no_validate
        )

        first_schema = LinkMLProcessor._load_schema_list(
            schemas, input_type=input_type
        )[0]
        processor = LinkMLProcessor(first_schema, validate=False)
        processor.save(concatenated_schema, output)
        console.print(f"[green]Successfully concatenated schemas to: {output}[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@main.command()
@click.option(
    "--schema",
    type=click.Path(exists=True),
    required=True,
    help="Path to the LinkML schema file",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "rdf", "graphql", "all"]),
    required=True,
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    required=True,
    help="Output file path (for 'all' format, this will be used as base name)",
)
@click.option(
    "--rdf-format",
    type=click.Choice(["turtle", "xml", "n3", "nt"]),
    default="turtle",
    help="RDF serialization format (only used with --format rdf)",
)
def export(schema, format, output, rdf_format):
    """Export LinkML schema to various formats."""
    try:
        exporter = SchemaExporter(schema)
        output_path = Path(output)

        if format == "all":
            # Export to all formats
            exporter.to_json_schema(output_path.with_suffix(".json"))
            exporter.to_rdf(output_path.with_suffix(".ttl"), format="turtle")
            exporter.to_graphql(output_path.with_suffix(".graphql"))
            console.print("[green]Successfully exported schema to all formats[/green]")
        else:
            if format == "json":
                exporter.to_json_schema(output_path)
            elif format == "rdf":
                exporter.to_rdf(output_path, format=rdf_format)
            elif format == "graphql":
                exporter.to_graphql(output_path)

            console.print(
                f"[green]Successfully exported schema to {format} format[/green]"
            )
    except Exception as e:
        console.print(f"[red]Error during export:[/red] {str(e)}")
        sys.exit(1)


def display_summary(schema_name: str, summary_data: dict, detailed: bool = False):
    """Display schema summary in a formatted table."""
    if detailed:
        for section_name, section_items in summary_data.items():
            display_detailed_section(section_name, section_items)
    else:
        table = Table(title=f"Schema Summary: {schema_name}")
        table.add_column("Section", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Items", style="yellow")

        for section_name, items in summary_data.items():
            table.add_row(section_name.capitalize(), str(len(items)), ", ".join(items))

        console.print(table)


def display_detailed_section(section_name: str, section_items: dict):
    """Display detailed information for a schema section."""
    console.print(f"\n[bold cyan]{section_name.capitalize()}[/bold cyan]")

    if not section_items:
        console.print("  No items found")
        return

    table = Table(show_header=True, box=None)

    if section_name == "classes":
        table.add_column("Name", style="green")
        table.add_column("Slots", style="yellow")
        table.add_column("Is A", style="yellow")
        table.add_column("Description")

        for name, details in section_items.items():
            table.add_row(
                name,
                ", ".join(details["slots"]),
                details["is_a"],
                details["description"],
            )

    elif section_name == "slots":
        table.add_column("Name", style="green")
        table.add_column("Range", style="yellow")
        table.add_column("Required", style="yellow")
        table.add_column("Multivalued", style="yellow")
        table.add_column("Description")

        for name, details in section_items.items():
            table.add_row(
                name,
                details["range"],
                str(details["required"]),
                str(details["multivalued"]),
                details["description"],
            )

    elif section_name == "enums":
        table.add_column("Name", style="green")
        table.add_column("Values", style="yellow")
        table.add_column("Description")

        for name, details in section_items.items():
            table.add_row(
                name, ", ".join(details["permissible_values"]), details["description"]
            )

    elif section_name == "types":
        table.add_column("Name", style="green")
        table.add_column("Base", style="yellow")
        table.add_column("URI", style="yellow")
        table.add_column("Description")

        for name, details in section_items.items():
            table.add_row(name, details["base"], details["uri"], details["description"])

    console.print(table)


if __name__ == "__main__":
    main()
