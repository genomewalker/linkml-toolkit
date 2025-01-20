"""Utility functions for the LinkML Toolkit."""

import logging
from pathlib import Path
from typing import List, Union, Dict, Any
import yaml

logger = logging.getLogger(__name__)


def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a YAML file safely."""
    try:
        with open(file_path) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML file {file_path}: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error reading file {file_path}: {str(e)}")


def save_yaml(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """Save data to a YAML file."""
    try:
        with open(file_path, "w") as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True)
    except Exception as e:
        raise ValueError(f"Error writing to file {file_path}: {str(e)}")


def resolve_imports(
    schema: Dict[str, Any], base_path: Union[str, Path]
) -> Dict[str, Any]:
    """Resolve schema imports and merge them into the main schema."""
    base_path = Path(base_path).parent
    resolved_schema = schema.copy()

    if "imports" in schema:
        for import_path in schema["imports"]:
            if import_path.startswith("http"):
                logger.warning(f"Skipping remote import: {import_path}")
                continue

            import_file = base_path / import_path
            if not import_file.exists():
                raise ValueError(f"Import file not found: {import_file}")

            imported_schema = load_yaml(import_file)
            # Merge imported definitions
            for section in ["classes", "slots", "types", "enums"]:
                if section in imported_schema:
                    resolved_schema.setdefault(section, {}).update(
                        imported_schema[section]
                    )

    return resolved_schema
