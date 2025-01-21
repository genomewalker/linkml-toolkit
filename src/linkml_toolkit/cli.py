import click
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich import box
from pathlib import Path
import logging
import sys
import json
from typing import List, Optional, Dict, Union
from datetime import datetime

from .core import LinkMLProcessor
from .validation import SchemaValidator
from .export import SchemaExporter
from .visualization.core import SchemaVisualizer, VisualizationConfig

console = Console()


def setup_logging(quiet: bool):
    """Setup logging configuration."""
    if quiet:
        logging.basicConfig(level=logging.WARNING, handlers=[logging.NullHandler()])
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")


def display_class_info(info: Dict, detailed: bool = False):
    """Display information about a class in a well-formatted manner."""
    console = Console()
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("Attribute", style="cyan")
    table.add_column("Value", style="white")

    # Class name and description
    console.print(f"\n[bold blue]Class: {info.get('name', 'Unknown')}[/bold blue]")

    # Add description if exists
    if info.get("description"):
        table.add_row("[bold]Description[/bold]", info["description"])

    # Inheritance information
    if info.get("is_a"):
        table.add_row("[bold]Inherits from[/bold]", info["is_a"])

    # Mixins
    if info.get("mixins"):
        table.add_row("[bold]Mixins[/bold]", ", ".join(info["mixins"]))

    # Abstract status
    table.add_row("[bold]Abstract[/bold]", "Yes" if info.get("abstract") else "No")

    # Render table of essential info
    console.print(table)

    # Slots section
    if info.get("slots"):
        console.print("\n[bold]Slots:[/bold]")
        slots_table = Table(show_header=True, header_style="bold magenta")
        slots_table.add_column("Name", style="cyan")
        slots_table.add_column("Range", style="green")
        slots_table.add_column("Required", style="yellow")
        slots_table.add_column("Inherited", style="red")

        for slot_name, slot_info in info["slots"].items():
            slots_table.add_row(
                slot_name,
                slot_info.get("range", "N/A"),
                "✓" if slot_info.get("required") else "✗",
                "✓" if slot_info.get("inherited") else "✗",
            )

        console.print(slots_table)

    # Detailed mode additional information
    if detailed:
        detailed_table = Table(show_header=False, box=box.SIMPLE)
        detailed_table.add_column("Attribute", style="cyan")
        detailed_table.add_column("Value", style="white")

        # Collect and display additional properties
        excluded_attrs = {"name", "description", "is_a", "mixins", "abstract", "slots"}
        remaining_attrs = {
            k: v
            for k, v in info.items()
            if k not in excluded_attrs and not k.startswith("_") and v is not None
        }

        if remaining_attrs:
            console.print("\n[bold]Additional Properties:[/bold]")
            for key, value in remaining_attrs.items():
                detailed_table.add_row(key, str(value))

            console.print(detailed_table)

    console.print()


def display_slot_info(info: Dict, detailed: bool = False):
    """Display information about a slot in a well-formatted manner."""
    console = Console()
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("Attribute", style="cyan")
    table.add_column("Value", style="white")

    # Slot name and description
    console.print(f"\n[bold blue]Slot: {info.get('name', 'Unknown')}[/bold blue]")

    # Add description if exists
    if info.get("description"):
        table.add_row("[bold]Description[/bold]", info["description"])

    # Primary attributes
    primary_attrs = [
        ("Range", "range"),
        ("Required", "required"),
        ("Multivalued", "multivalued"),
        ("Pattern", "pattern"),
    ]

    for label, attr in primary_attrs:
        if attr in info:
            value = (
                "Yes" if isinstance(info[attr], bool) and info[attr] else str(info[attr]) or "N/A"
            )
            table.add_row(f"[bold]{label}[/bold]", value)

    # Value constraints
    constraints = []
    if info.get("min_value") is not None:
        constraints.append(f"Minimum: {info['min_value']}")
    if info.get("max_value") is not None:
        constraints.append(f"Maximum: {info['max_value']}")

    if constraints:
        table.add_row("[bold]Value Constraints[/bold]", ", ".join(constraints))

    # Render primary info table
    console.print(table)

    # Usage information
    if "usage" in info and info["usage"]:
        console.print("\n[bold]Used in Classes:[/bold]")
        usage_table = Table(show_header=True, header_style="bold magenta")
        usage_table.add_column("Class", style="cyan")
        usage_table.add_column("Inherited", style="red")
        usage_table.add_column("Overrides", style="green")

        for class_name, usage in info["usage"].items():
            overrides = (
                ", ".join(f"{k}: {v}" for k, v in usage.get("overrides", {}).items())
                if usage.get("overrides")
                else "N/A"
            )
            usage_table.add_row(class_name, "✓" if usage.get("inherited") else "✗", overrides)

        console.print(usage_table)

    # Detailed mode additional information
    if detailed:
        # Annotations
        if info.get("annotations"):
            console.print("\n[bold]Annotations:[/bold]")
            annotations_table = Table(show_header=True, header_style="bold magenta")
            annotations_table.add_column("Key", style="cyan")
            annotations_table.add_column("Value", style="white")

            for key, value in info["annotations"].items():
                annotations_table.add_row(str(key), str(value))

            console.print(annotations_table)

        # Examples
        if info.get("examples"):
            console.print("\n[bold]Examples:[/bold]")
            examples_table = Table(show_header=True, header_style="bold magenta")
            examples_table.add_column("Example", style="white")

            for example in info["examples"]:
                if isinstance(example, dict):
                    examples_table.add_row("\n".join(f"{k}: {v}" for k, v in example.items()))
                else:
                    examples_table.add_row(str(example))

            console.print(examples_table)

        # Additional properties
        additional_attrs = {
            k: v
            for k, v in info.items()
            if k
            not in {
                "name",
                "description",
                "range",
                "required",
                "multivalued",
                "pattern",
                "min_value",
                "max_value",
                "usage",
                "annotations",
                "examples",
            }
            and not k.startswith("_")
            and v is not None
        }

        if additional_attrs:
            console.print("\n[bold]Additional Properties:[/bold]")
            additional_table = Table(show_header=True, header_style="bold magenta")
            additional_table.add_column("Attribute", style="cyan")
            additional_table.add_column("Value", style="white")

            for key, value in additional_attrs.items():
                additional_table.add_row(str(key), str(value))

            console.print(additional_table)

    console.print()


def display_enum_info(info: Dict, detailed: bool = False):
    """Display information about an enum in a well-formatted manner."""
    console = Console()

    # Enum name and description
    console.print(f"\n[bold blue]Enum: {info.get('name', 'Unknown')}[/bold blue]")

    # Description
    if info.get("description"):
        console.print(f"\n[bold]Description:[/bold]\n{info['description']}")

    # Permissible Values
    if info.get("permissible_values"):
        console.print("\n[bold]Permissible Values:[/bold]")
        values_table = Table(show_header=True, header_style="bold magenta")
        values_table.add_column("Value", style="cyan")

        # Add additional columns in detailed mode
        if detailed:
            values_table.add_column("Description", style="white")
            values_table.add_column("Additional Info", style="green")

        for value_name, value_info in info["permissible_values"].items():
            if detailed and isinstance(value_info, dict):
                # Prepare additional info columns
                description = value_info.get("description", "N/A")

                # Collect any other meaningful info
                additional_info = (
                    ", ".join(
                        f"{k}: {v}"
                        for k, v in value_info.items()
                        if k not in {"name", "description"}
                    )
                    or "N/A"
                )

                values_table.add_row(value_name, description, additional_info)
            else:
                values_table.add_row(value_name)

        console.print(values_table)

    # Detailed mode additional properties
    if detailed:
        # Collect additional attributes
        additional_attrs = {
            k: v
            for k, v in info.items()
            if k not in {"name", "description", "permissible_values"}
            and not k.startswith("_")
            and v is not None
        }

        if additional_attrs:
            console.print("\n[bold]Additional Properties:[/bold]")
            additional_table = Table(show_header=True, header_style="bold magenta")
            additional_table.add_column("Attribute", style="cyan")
            additional_table.add_column("Value", style="white")

            for key, value in additional_attrs.items():
                additional_table.add_row(str(key), str(value))

            console.print(additional_table)

    console.print()


def display_hierarchy(results: Dict, processor: LinkMLProcessor):
    """Display schema hierarchy as a tree."""
    console = Console()
    tree = Tree("[bold]Schema Class Hierarchy[/bold]")

    def add_class_node(parent_tree, class_name):
        """Add a class node to the tree with appropriate styling."""
        class_def = processor.schema_view.get_class(class_name)
        if not class_def:
            return

        # Determine node style based on class type
        if getattr(class_def, "mixin", False):
            style = "yellow italic"
            suffix = " (Mixin)"
        elif getattr(class_def, "abstract", False):
            style = "blue italic"
            suffix = " (Abstract)"
        else:
            style = "cyan"
            suffix = ""

        node = parent_tree.add(f"[{style}]{class_name}{suffix}[/{style}]")

        # Add child classes
        for child_name, child_def in processor.schema_view.all_classes().items():
            if getattr(child_def, "is_a", None) == class_name:
                add_class_node(node, child_name)

    # Start with root classes (those without is_a)
    root_classes = []
    for class_name, class_def in processor.schema_view.all_classes().items():
        if not getattr(class_def, "is_a", None):
            root_classes.append(class_name)

    # Add root classes to tree
    for root in sorted(root_classes):
        add_class_node(tree, root)

    console.print(tree)


def display_schema_analysis(results: Dict, detailed: bool = False):
    """Display schema analysis results in a well-formatted manner."""
    console = Console()

    # Schema metadata
    console.print(f"\n[bold blue]Schema:[/bold blue] {results.get('name', 'Unknown')}")
    if results.get("version"):
        console.print(f"[bold]Version:[/bold] {results['version']}")

    if results.get("description"):
        console.print(f"\n[bold]Description:[/bold]\n{results['description']}")

    # Create summary table
    table = Table(show_header=True)
    table.add_column("Section", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_column("Items", style="yellow")

    # Add sections to table
    sections = ["classes", "slots", "enums", "types", "subsets"]
    for section in sections:
        if section in results:
            items = results[section]
            if isinstance(items, dict):
                count = len(items)
                if count > 0:
                    if detailed:
                        names = "\n".join(f"• {name}" for name in sorted(items.keys()))
                    else:
                        # Show only first 5 items in summary mode
                        sorted_items = sorted(items.keys())
                        if len(sorted_items) > 5:
                            names = (
                                ", ".join(sorted_items[:5])
                                + f" (and {len(sorted_items)-5} more...)"
                            )
                        else:
                            names = ", ".join(sorted_items)
            else:
                count = len(items)
                if count > 0:
                    if detailed:
                        names = "\n".join(f"• {name}" for name in sorted(items))
                    else:
                        # Show only first 5 items in summary mode
                        sorted_items = sorted(items)
                        if len(sorted_items) > 5:
                            names = (
                                ", ".join(sorted_items[:5])
                                + f" (and {len(sorted_items)-5} more...)"
                            )
                        else:
                            names = ", ".join(sorted_items)

            table.add_row(section.capitalize(), str(count), names if count > 0 else "none")

    console.print("\n")
    console.print(table)

    # Additional metadata only in detailed mode
    if detailed and results.get("prefixes"):
        console.print("\n[bold]Prefixes:[/bold]")
        for prefix, uri in results["prefixes"].items():
            console.print(f"  {prefix}: {uri}")

    if detailed:
        excluded_attrs = {
            "name",
            "version",
            "description",
            "prefixes",
            "classes",
            "slots",
            "enums",
            "types",
            "subsets",
        }
        remaining_attrs = {
            k: v for k, v in results.items() if k not in excluded_attrs and not k.startswith("_")
        }

        if remaining_attrs:
            console.print("\n[bold]Additional Metadata:[/bold]")
            for key, value in remaining_attrs.items():
                if isinstance(value, dict):
                    console.print(f"\n  [cyan]{key}:[/cyan]")
                    for k, v in value.items():
                        console.print(f"    {k}: {v}")
                else:
                    console.print(f"  [cyan]{key}:[/cyan] {value}")

    console.print()


@click.group()
@click.option("--quiet", "-q", is_flag=True, help="Suppress all output except errors")
@click.option("--strict", is_flag=True, help="Enable strict validation mode")
@click.version_option()
def main(quiet, strict):
    """LinkML Toolkit - A comprehensive toolkit for working with LinkML schemas."""
    setup_logging(quiet)
    ctx = click.get_current_context()
    ctx.ensure_object(dict)
    ctx.obj["quiet"] = quiet
    ctx.obj["strict"] = strict


@main.command()
@click.option(
    "--schema",
    type=click.Path(exists=True),
    required=True,
    help="Path to the LinkML schema file",
)
@click.option(
    "--entity",
    type=click.Choice(["class", "slot", "enum"], case_sensitive=False),
    help="Type of schema entity to analyze",
)
@click.option(
    "--name",
    help="Name of the specific entity to analyze",
)
@click.option(
    "--section",
    "-s",
    multiple=True,
    type=click.Choice(["classes", "slots", "enums", "types", "subsets"], case_sensitive=False),
    help="Sections to include in analysis (default: all)",
)
@click.option(
    "--detailed",
    "-d",
    is_flag=True,
    help="Show detailed information",
)
@click.option(
    "--include-inherited",
    "-i",
    is_flag=True,
    help="Include inherited properties",
)
@click.option(
    "--tree",
    "-t",
    is_flag=True,
    help="Show hierarchy as a tree",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save analysis to JSON file",
)
def analyze(
    schema,
    entity,
    name,
    section,
    detailed,
    include_inherited,
    tree,
    output,
):
    """Analyze a LinkML schema or specific elements within it."""
    try:
        ctx = click.get_current_context()
        quiet = ctx.obj.get("quiet", False)
        strict = ctx.obj.get("strict", False)

        # Validate schema loading
        try:
            processor = LinkMLProcessor(schema, validate=True, strict=strict)
            errors = processor.validator.validate_schema(schema)
            if errors:
                for error in errors:
                    severity = (
                        "[red]ERROR[/red]"
                        if error.severity == "ERROR"
                        else "[yellow]WARNING[/yellow]"
                    )
                    console.print(f"{severity}: {error.message}")
                    if error.details:
                        for key, value in error.details.items():
                            console.print(f"  {key}: {value}")
                if strict:
                    sys.exit(1)
                else:
                    console.print(
                        "[yellow]WARNING:[/yellow]Continuing with schema combination despite validation errors"
                    )

        except Exception as schema_load_error:
            console.print(f"[red]Error loading schema:[/red] {str(schema_load_error)}")
            sys.exit(1)

        # Specific entity analysis
        if entity and name:
            # Map entity to appropriate analysis and display functions
            entity_map = {
                "class": {
                    "analyze_func": lambda n: processor.analyze_class(n, include_inherited),
                    "display_func": display_class_info,
                    "not_found_msg": "Class",
                },
                "slot": {
                    "analyze_func": processor.analyze_slot,
                    "display_func": display_slot_info,
                    "not_found_msg": "Slot",
                },
                "enum": {
                    "analyze_func": processor.analyze_enum,
                    "display_func": display_enum_info,
                    "not_found_msg": "Enum",
                },
            }

            try:
                # Validate entity type
                entity_handler = entity_map.get(entity.lower())
                if not entity_handler:
                    console.print(
                        f"[red]Error:[/red] Invalid entity type '{entity}'. Choose from: class, slot, enum"
                    )
                    sys.exit(1)

                # Attempt to analyze specific entity
                try:
                    info = entity_handler["analyze_func"](name)
                except Exception as analyze_error:
                    console.print(
                        f"[red]Error analyzing {entity} '{name}':[/red] {str(analyze_error)}"
                    )
                    sys.exit(1)

                # Validate and display entity information
                if info:
                    try:
                        entity_handler["display_func"](info, detailed)
                    except Exception as display_error:
                        console.print(
                            f"[red]Error displaying {entity} '{name}':[/red] {str(display_error)}"
                        )
                        sys.exit(1)
                else:
                    console.print(
                        f"[red]Error:[/red] {entity_handler['not_found_msg']} '{name}' not found"
                    )
                    sys.exit(1)

            except Exception as entity_error:
                console.print(f"[red]Error processing {entity} '{name}':[/red] {str(entity_error)}")
                sys.exit(1)

        # Entire schema analysis
        else:
            try:
                # Analyze schema sections
                sections = list(section) if section else None
                results = processor.analyze_schema(sections=sections, detailed=detailed)

                # Display results
                try:
                    if tree:
                        display_hierarchy(results, processor)
                    else:
                        display_schema_analysis(results, detailed)
                except Exception as display_error:
                    console.print(
                        f"[red]Error displaying schema analysis:[/red] {str(display_error)}"
                    )
                    sys.exit(1)

                # Optional output to JSON
                if output:
                    try:
                        output_path = Path(output)

                        # Prepare JSON-serializable results
                        json_results = results.copy()
                        json_results = json.loads(
                            json.dumps(json_results, default=lambda o: str(o))
                        )

                        with open(output_path, "w", encoding="utf-8") as f:
                            json.dump(json_results, f, indent=2, ensure_ascii=False)

                        if not quiet:
                            console.print(f"\n[green]Analysis saved as JSON to: {output}[/green]")
                    except Exception as output_error:
                        console.print(
                            f"[red]Error saving output to JSON:[/red] {str(output_error)}"
                        )
                        sys.exit(1)

            except Exception as schema_analysis_error:
                console.print(f"[red]Error analyzing schema:[/red] {str(schema_analysis_error)}")
                sys.exit(1)

    except Exception as unexpected_error:
        console.print(f"[red]Unexpected error:[/red] {str(unexpected_error)}")
        sys.exit(1)


@main.command()
@click.option(
    "--schema",
    type=click.Path(exists=True),
    required=True,
    help="Path to the LinkML schema file",
)
@click.option("--metadata", is_flag=True, help="Show schema metadata")
def validate(schema, metadata):
    """Validate a schema file."""
    ctx = click.get_current_context()
    quiet = ctx.obj.get("quiet", False)
    strict = ctx.obj.get("strict", False)

    try:
        processor = LinkMLProcessor(schema, validate=True, strict=strict)
        errors = processor.validator.validate_schema(schema)

        if errors:
            for error in errors:
                severity = (
                    "[red]ERROR[/red]" if error.severity == "ERROR" else "[yellow]WARNING[/yellow]"
                )
                console.print(f"{severity}: {error.message}")
                if error.details:
                    for key, value in error.details.items():
                        console.print(f"  {key}: {value}")
            if strict or any(e.severity == "ERROR" for e in errors):
                sys.exit(1)
        elif not quiet:
            console.print("[green]Schema validation passed - no errors found.[/green]")

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
    type=click.Choice(["json", "rdf", "graphql", "csv", "tsv", "sql"]),
    required=True,
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    required=True,
    help="Output file path",
)
@click.option(
    "--rdf-format",
    type=click.Choice(["turtle", "xml", "n3", "nt"]),
    default="turtle",
    help="RDF serialization format",
)
@click.option(
    "--sql-dialect",
    type=click.Choice(["postgresql", "mysql", "sqlite", "duckdb"]),
    default="postgresql",
    help="SQL dialect to use",
)
def export(schema, format, output, rdf_format, sql_dialect):
    """Export schema to various formats."""
    ctx = click.get_current_context()
    quiet = ctx.obj.get("quiet", False)
    strict = ctx.obj.get("strict", False)

    try:
        # Validate schema
        validator = SchemaValidator(schema, strict=strict)
        errors = validator.validate_schema(schema)
        if errors:
            for error in errors:
                severity = (
                    "[red]ERROR[/red]" if error.severity == "ERROR" else "[yellow]WARNING[/yellow]"
                )
                console.print(f"{severity}: {error.message}")
                if error.details:
                    for key, value in error.details.items():
                        console.print(f"  {key}: {value}")
            if strict:
                sys.exit(1)
            else:
                console.print(
                    "[yellow]WARNING:[/yellow]Continuing with schema combination despite validation errors"
                )

        exporter = SchemaExporter(schema)
        output_path = Path(output)

        if format == "json":
            exporter.to_json_schema(output_path)
        elif format == "rdf":
            exporter.to_rdf(output_path, format=rdf_format)
        elif format == "graphql":
            exporter.to_graphql(output_path)
        elif format in ["csv", "tsv"]:
            delimiter = "\t" if format == "tsv" else ","
            exporter.to_csv(output_path, delimiter=delimiter)
        elif format == "sql":
            exporter.to_sql(output_path, dialect=sql_dialect)

        if not quiet:
            console.print(
                f"[green]Successfully exported schema to {format} format: {output}[/green]"
            )

    except Exception as e:
        console.print(f"[red]Error during export:[/red] {str(e)}")
        sys.exit(1)


@main.command()
@click.option(
    "--schema",
    type=click.Path(exists=True),
    required=True,
    help="Path to the source LinkML schema file",
)
@click.option(
    "--classes",
    "-c",
    required=True,
    help="Comma-separated list of classes to include in the subset",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    required=True,
    help="Output path for the subset schema",
)
@click.option(
    "--no-inherited",
    is_flag=True,
    help="Exclude inherited slots and parent classes",
)
def subset(schema, classes, output, no_inherited):
    """Create a subset of a LinkML schema containing specified classes."""
    ctx = click.get_current_context()
    quiet = ctx.obj.get("quiet", False)
    strict = ctx.obj.get("strict", False)

    try:
        # Split classes and trim whitespace
        class_list = [c.strip() for c in classes.split(",")]

        # Process schema with optional validation
        processor = LinkMLProcessor(schema, validate=True, strict=strict)

        # Create subset
        subset_schema = processor.subset_schema(
            class_names=class_list, include_inherited=not no_inherited
        )

        # Save subset
        processor.save(subset_schema, output)

        if not quiet:
            console.print(
                f"[green]Successfully created schema subset with classes: {', '.join(class_list)}[/green]"
            )
            console.print(f"[green]Saved to: {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error creating schema subset:[/red] {str(e)}")
        sys.exit(1)


@main.command()
@click.option(
    "--schema",
    type=click.Path(exists=True),
    required=True,
    help="Path to the first schema file",
)
@click.option(
    "--additional-schemas",
    "-a",
    multiple=True,
    type=click.Path(exists=True),
    help="Additional schema files to combine",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    required=True,
    help="Output file path for combined schema",
)
@click.option(
    "--mode",
    type=click.Choice(["merge", "concat"]),
    default="merge",
    help="How to combine schemas",
)
def combine(schema, additional_schemas, output, mode):
    """Combine multiple schemas (merge or concatenate)."""
    ctx = click.get_current_context()
    quiet = ctx.obj.get("quiet", False)
    strict = ctx.obj.get("strict", False)

    try:
        all_schemas = [schema] + list(additional_schemas)
        schema_list = ",".join(str(s) for s in all_schemas)

        if mode == "merge":
            result, errors = LinkMLProcessor.merge_multiple(
                schema_list, validate=True, strict=strict, return_errors=True
            )
        else:  # concat
            result, errors = LinkMLProcessor.concat_multiple(
                schema_list, validate=True, strict=strict, return_errors=True
            )

        if errors:
            for schema_path, schema_errors in errors.items():
                console.print(f"\n[bold red]Validation errors in schema: {schema_path}[/bold red]")
                for error in schema_errors:
                    severity = (
                        "[red]ERROR[/red]"
                        if error.severity == "ERROR"
                        else "[yellow]WARNING[/yellow]"
                    )
                    console.print(f"{severity}: {error.message}")
                    if error.details:
                        for key, value in error.details.items():
                            console.print(f"  {key}: {value}")
            if strict:
                sys.exit(1)
            else:
                console.print(
                    "[yellow]WARNING:[/yellow]Continuing with schema combination despite validation errors"
                )

        processor = LinkMLProcessor(schema, validate=False)
        processor.save(result, output)

        if not quiet:
            msg = "merged" if mode == "merge" else "concatenated"
            console.print(f"[green]Successfully {msg} schemas to: {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error combining schemas:[/red] {str(e)}")
        sys.exit(1)


@main.command()
@click.option(
    "--schema",
    type=click.Path(exists=True),
    required=True,
    help="Path to the LinkML schema file",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    required=True,
    help="Output directory or file path for schema visualization",
)
@click.option(
    "--full-docs/--single-page",
    default=False,
    help="Generate full documentation bundle or single visualization page",
)
@click.option(
    "--show-descriptions/--hide-descriptions",
    default=True,
    help="Show or hide descriptions in the visualization",
)
@click.option(
    "--show-inheritance/--hide-inheritance",
    default=True,
    help="Show or hide inheritance relationships",
)
@click.option(
    "--show-stats/--hide-stats",
    default=True,
    help="Show or hide usage statistics",
)
def visualize(schema, output, full_docs, show_descriptions, show_inheritance, show_stats):
    """Generate an interactive HTML visualization of the schema."""
    ctx = click.get_current_context()
    quiet = ctx.obj.get("quiet", False)
    strict = ctx.obj.get("strict", False)

    try:
        # Initialize processor
        processor = LinkMLProcessor(schema, validate=True, strict=strict)
        output_path = Path(output)

        # Create visualization config
        from .visualization.core import VisualizationConfig

        config = VisualizationConfig(
            show_descriptions=show_descriptions,
            show_inheritance=show_inheritance,
        )

        # Initialize visualizer
        visualizer = SchemaVisualizer(processor, config=config)

        if full_docs:
            # Generate full documentation bundle
            output_path.mkdir(parents=True, exist_ok=True)
            visualizer.generate_documentation(output_path)
            if not quiet:
                console.print(
                    f"[green]Successfully generated documentation bundle in: {output_path}[/green]"
                )
        else:
            # Generate single visualization page
            if output_path.is_dir() or output_path.suffix == "":
                output_path.mkdir(parents=True, exist_ok=True)
                html_path = output_path / "schema_visualization.html"
            else:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                html_path = output_path

            visualizer.generate_visualization(output_path=html_path)
            if not quiet:
                console.print(
                    f"[green]Successfully generated schema visualization in: {html_path}[/green]"
                )

    except Exception as e:
        console.print(f"[red]Error generating schema visualization:[/red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
