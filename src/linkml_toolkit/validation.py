"""Schema validation functionality."""

from typing import Dict, List, Optional, Union
from pathlib import Path
import logging
from dataclasses import dataclass
import yaml
from linkml_runtime.utils.schemaview import SchemaView
from linkml_runtime.utils.validation import ValidationResult, validate_schema
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class ValidationError:
    path: str
    message: str
    severity: str
    details: Optional[Dict] = None


class SchemaValidator:
    def __init__(self, quiet: bool = False):
        """Initialize the schema validator."""
        self.quiet = quiet

    def validate_schema(self, schema_path: Union[str, Path]) -> List[ValidationError]:
        """Validate a LinkML schema file."""
        schema_path = Path(schema_path)
        errors = []

        try:
            # Load and parse the YAML first
            try:
                with open(schema_path) as f:
                    schema_dict = yaml.safe_load(f)
            except yaml.YAMLError as e:
                errors.append(
                    ValidationError(
                        path=str(schema_path),
                        message=f"Invalid YAML syntax: {str(e)}",
                        severity="ERROR",
                    )
                )
                return errors

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

            # Required top-level fields
            required_fields = ["name", "id"]
            for field in required_fields:
                if field not in schema_dict:
                    errors.append(
                        ValidationError(
                            path=str(schema_path),
                            message=f"Missing required field: {field}",
                            severity="ERROR",
                        )
                    )

            # Validate using LinkML's validation utilities
            try:
                schema_view = SchemaView(str(schema_path))
                validation_result = validate_schema(schema_view.schema)

                if not validation_result.valid:
                    for error in validation_result.results:
                        errors.append(
                            ValidationError(
                                path=str(schema_path),
                                message=error.message,
                                severity="ERROR",
                                details=(
                                    {"location": error.location}
                                    if error.location
                                    else None
                                ),
                            )
                        )

                # Additional validations using SchemaView
                self._validate_references(schema_view, errors, schema_path)

            except Exception as e:
                errors.append(
                    ValidationError(
                        path=str(schema_path),
                        message=f"Schema validation error: {str(e)}",
                        severity="ERROR",
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

    def _validate_references(
        self, schema_view: SchemaView, errors: List[ValidationError], schema_path: Path
    ):
        """Validate references between schema elements."""
        # Check slot references in classes
        for class_name, class_def in schema_view.all_classes().items():
            for slot_name in class_def.slots:
                if not schema_view.get_slot(slot_name):
                    errors.append(
                        ValidationError(
                            path=str(schema_path),
                            message=f"Class '{class_name}' references undefined slot '{slot_name}'",
                            severity="ERROR",
                            details={"class": class_name, "slot": slot_name},
                        )
                    )

        # Check range references
        for slot_name, slot_def in schema_view.all_slots().items():
            if slot_def.range:
                range_name = slot_def.range
                if not (
                    schema_view.get_type(range_name)
                    or schema_view.get_class(range_name)
                    or schema_view.get_enum(range_name)
                ):
                    errors.append(
                        ValidationError(
                            path=str(schema_path),
                            message=f"Slot '{slot_name}' references undefined range '{range_name}'",
                            severity="ERROR",
                            details={"slot": slot_name, "range": range_name},
                        )
                    )

    def format_errors(self, errors: List[ValidationError]) -> str:
        """Format validation errors into a readable string."""
        if not errors:
            return "No validation errors found."

        formatted = []
        for error in errors:
            message = f"[red]ERROR[/red]: {error.message}"
            if error.details:
                details = "\n".join(f"  {k}: {v}" for k, v in error.details.items())
                message += f"\n{details}"
            formatted.append(message)

        return "\n".join(formatted)

    def validate_multiple(
        self, schema_paths: List[Path]
    ) -> Dict[str, List[ValidationError]]:
        """Validate multiple schema files."""
        results = {}
        for path in schema_paths:
            if not self.quiet:
                logger.info(f"Validating schema: {path}")
            results[str(path)] = self.validate_schema(path)
        return results
