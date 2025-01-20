"""Schema validation functionality."""

from typing import Dict, List, Optional, Union, Set
from pathlib import Path
import logging
from dataclasses import dataclass
import yaml
from rich.console import Console
from linkml_runtime.utils.schemaview import SchemaView
from linkml_runtime.linkml_model import SchemaDefinition

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class ValidationError:
    path: str
    message: str
    severity: str
    details: Optional[Dict] = None


class SchemaValidator:
    """Schema validator for LinkML schemas."""

    def __init__(self, quiet: bool = False, strict: bool = False):
        """Initialize the schema validator."""
        self.quiet = quiet
        self.strict = strict

    def validate_schema(self, schema_path: Union[str, Path]) -> List[ValidationError]:
        """Validate a LinkML schema file with configurable strictness."""
        schema_path = Path(schema_path)
        errors = []

        try:
            # Load and parse the YAML
            schema_dict = self._load_yaml(schema_path)

            # Basic structure validation
            if not isinstance(schema_dict, dict):
                errors.append(
                    ValidationError(
                        path=str(schema_path),
                        message="Schema must be a YAML dictionary",
                        severity="ERROR",
                    )
                )
                return errors

            # Validate minimal required fields
            if "name" not in schema_dict:
                errors.append(
                    ValidationError(
                        path=str(schema_path),
                        message="Schema must have a 'name' field",
                        severity="WARNING",
                    )
                )
                schema_dict["name"] = schema_path.stem

            if "id" not in schema_dict:
                errors.append(
                    ValidationError(
                        path=str(schema_path),
                        message="Schema should have an 'id' field",
                        severity="WARNING",
                    )
                )
                schema_dict["id"] = f"https://w3id.org/linkml/{schema_dict['name']}"

            # Create SchemaDefinition and SchemaView
            try:
                schema_def = SchemaDefinition(**schema_dict)
                schema_view = SchemaView(schema_def)
                content_errors = self._validate_schema_contents(schema_view, schema_path)
                errors.extend(content_errors)
            except Exception as e:
                severity = "ERROR" if self.strict else "WARNING"
                errors.append(
                    ValidationError(
                        path=str(schema_path),
                        message=str(e),
                        severity=severity,
                    )
                )

        except Exception as e:
            errors.append(
                ValidationError(
                    path=str(schema_path),
                    message=f"Unexpected error during validation: {str(e)}",
                    severity="ERROR",
                )
            )

        return errors

    def _load_yaml(self, path: Path) -> dict:
        """Load and parse YAML file."""
        try:
            with open(path) as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")

    def _validate_schema_contents(
        self, schema_view: SchemaView, schema_path: Path
    ) -> List[ValidationError]:
        """Validate schema contents."""
        errors = []

        try:
            # Validate class references
            for class_name, class_def in schema_view.all_classes().items():
                if hasattr(class_def, "slots"):
                    for slot_name in class_def.slots or []:
                        if not schema_view.get_slot(slot_name):
                            errors.append(
                                ValidationError(
                                    path=str(schema_path),
                                    message=f"Class '{class_name}' references undefined slot '{slot_name}'",
                                    severity="ERROR",
                                    details={"class": class_name, "slot": slot_name},
                                )
                            )

                # Validate inheritance
                if hasattr(class_def, "is_a") and class_def.is_a:
                    if not schema_view.get_class(class_def.is_a):
                        errors.append(
                            ValidationError(
                                path=str(schema_path),
                                message=f"Class '{class_name}' inherits from undefined class '{class_def.is_a}'",
                                severity="ERROR",
                                details={"class": class_name, "parent": class_def.is_a},
                            )
                        )

            # Validate slot ranges
            for slot_name, slot_def in schema_view.all_slots().items():
                if hasattr(slot_def, "range") and slot_def.range:
                    range_name = slot_def.range
                    if not self._is_valid_range(range_name, schema_view):
                        errors.append(
                            ValidationError(
                                path=str(schema_path),
                                message=f"Slot '{slot_name}' references undefined range '{range_name}'",
                                severity="ERROR",
                                details={"slot": slot_name, "range": range_name},
                            )
                        )

                # Validate domain
                if hasattr(slot_def, "domain") and slot_def.domain:
                    if not schema_view.get_class(slot_def.domain):
                        errors.append(
                            ValidationError(
                                path=str(schema_path),
                                message=f"Slot '{slot_name}' references undefined domain '{slot_def.domain}'",
                                severity="ERROR",
                                details={"slot": slot_name, "domain": slot_def.domain},
                            )
                        )

        except Exception as e:
            if self.strict:
                raise
            logger.debug(f"Non-critical validation error: {str(e)}")

        return errors

    def _is_valid_range(self, range_name: str, schema_view: SchemaView) -> bool:
        """Check if a range type is valid."""
        builtin_types = {
            "string",
            "integer",
            "boolean",
            "datetime",
            "date",
            "time",
            "float",
            "double",
            "decimal",
            "uri",
            "uriorcurie",
            "ncname",
            "objectidentifier",
            "nodeidentifier",
        }
        return (
            range_name in builtin_types
            or schema_view.get_type(range_name) is not None
            or schema_view.get_class(range_name) is not None
            or schema_view.get_enum(range_name) is not None
        )

    def validate_multiple(self, schema_paths: List[Path]) -> Dict[str, List[ValidationError]]:
        """Validate multiple schema files."""
        results = {}
        for path in schema_paths:
            if not self.quiet:
                logger.info(f"Validating schema: {path}")
            results[str(path)] = self.validate_schema(path)
        return results

    def format_errors(self, errors: List[ValidationError]) -> str:
        """Format validation errors into a readable string."""
        if not errors:
            return "No validation errors found."

        formatted = []
        for error in errors:
            if error.severity == "ERROR":
                msg = f"[red]{error.severity}[/red]: {error.message}"
            else:
                msg = f"[yellow]{error.severity}[/yellow]: {error.message}"

            if error.details:
                details = "\n".join(f"  {k}: {v}" for k, v in error.details.items())
                msg += f"\n{details}"
            formatted.append(msg)

        return "\n".join(formatted)


def display_validation_errors(errors):
    """Display validation errors with proper formatting."""
    console = Console()

    error_found = False
    warning_found = False

    # Group by severity
    error_messages = []
    warning_messages = []

    for error in errors:
        if error.severity == "ERROR":
            error_found = True
            msg_lines = [error.message]
            if error.details:
                for key, value in error.details.items():
                    msg_lines.append(f"  {key}: {value}")
            error_messages.append(msg_lines)
        else:
            warning_found = True
            msg_lines = [error.message]
            if error.details:
                for key, value in error.details.items():
                    msg_lines.append(f"  {key}: {value}")
            warning_messages.append(msg_lines)

    # Display errors and warnings
    if error_found or warning_found:
        console.print("Validation Issues:", style="bold red")
        for msg_lines in error_messages + warning_messages:
            for i, line in enumerate(msg_lines):
                style = "red" if i == 0 else "dim"
                console.print(f"• {line}", style=style)

    # Return True if any issues are found
    return error_found or warning_found
