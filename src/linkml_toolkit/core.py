"""Core functionality for the LinkML Toolkit."""

from pathlib import Path
from typing import Dict, List, Union, Optional
import logging
from rich.progress import Progress, SpinnerColumn, TextColumn
from .validation import SchemaValidator
from .utils import load_yaml, save_yaml, resolve_imports

logger = logging.getLogger(__name__)


class LinkMLProcessor:
    def __init__(
        self, schema_path: Union[str, Path], quiet: bool = False, validate: bool = True
    ):
        """Initialize the processor with a schema file."""
        self.schema_path = Path(schema_path)
        self.quiet = quiet
        self.validator = SchemaValidator(quiet=quiet)

        if validate:
            self._validate_schema()

        self.schema = self._load_schema()
        if not quiet:
            logger.info(f"Loaded schema from {self.schema_path}")

    def _validate_schema(self):
        """Validate the schema and raise an error if validation fails."""
        errors = self.validator.validate_schema(self.schema_path)
        if errors:
            error_str = self.validator.format_errors(errors)
            raise ValueError(f"Schema validation failed:\n{error_str}")

    def _load_schema(self) -> Dict:
        """Load the LinkML schema from file."""
        schema = load_yaml(self.schema_path)
        return resolve_imports(schema, self.schema_path)

    @staticmethod
    def _load_schema_list(schema_list: str, input_type: str = "auto") -> List[Path]:
        """Load a list of schemas from either a comma-separated string or a file."""
        if input_type == "file" or (input_type == "auto" and not "," in schema_list):
            try:
                list_path = Path(schema_list)
                with open(list_path) as f:
                    paths = [
                        Path(line.strip())
                        for line in f
                        if line.strip() and not line.startswith("#")
                    ]
                if not paths:
                    raise ValueError(
                        f"No valid schema paths found in file: {schema_list}"
                    )
                return paths
            except FileNotFoundError as e:
                if input_type == "file":
                    raise FileNotFoundError(
                        f"Schema list file not found: {schema_list}"
                    ) from e
                if input_type != "auto":
                    raise

        if input_type == "list" or input_type == "auto":
            paths = [Path(s.strip()) for s in schema_list.split(",") if s.strip()]
            if not paths:
                raise ValueError("No valid schema paths found in comma-separated list")
            return paths

        raise ValueError(
            f"Invalid input_type: {input_type}. Must be one of 'auto', 'file', or 'list'"
        )

    def get_summary(self, sections: List[str] = None, detailed: bool = False) -> Dict:
        """Generate a summary of the schema."""
        all_sections = {
            "classes": self.schema.get("classes", {}),
            "slots": self.schema.get("slots", {}),
            "enums": self.schema.get("enums", {}),
            "types": self.schema.get("types", {}),
        }

        if sections:
            invalid_sections = set(sections) - set(all_sections.keys())
            if invalid_sections:
                raise ValueError(f"Invalid sections: {', '.join(invalid_sections)}")
            sections_to_show = {k: v for k, v in all_sections.items() if k in sections}
        else:
            sections_to_show = all_sections

        if detailed:
            summary = {}
            for section, items in sections_to_show.items():
                section_details = {}
                for name, item in items.items():
                    if section == "classes":
                        section_details[name] = {
                            "description": item.get("description", ""),
                            "slots": item.get("slots", []),
                            "is_a": item.get("is_a", ""),
                            "mixins": item.get("mixins", []),
                        }
                    elif section == "slots":
                        section_details[name] = {
                            "description": item.get("description", ""),
                            "range": item.get("range", ""),
                            "required": item.get("required", False),
                            "multivalued": item.get("multivalued", False),
                            "pattern": item.get("pattern", ""),
                        }
                    elif section == "enums":
                        section_details[name] = {
                            "description": item.get("description", ""),
                            "permissible_values": list(
                                item.get("permissible_values", {}).keys()
                            ),
                        }
                    elif section == "types":
                        section_details[name] = {
                            "description": item.get("description", ""),
                            "base": item.get("base", ""),
                            "uri": item.get("uri", ""),
                        }
                summary[section] = section_details
        else:
            summary = {
                section: list(items.keys())
                for section, items in sections_to_show.items()
            }

        return summary
