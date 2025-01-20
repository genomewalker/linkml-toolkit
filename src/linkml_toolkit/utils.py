# File: src/linkml_toolkit/utils.py
"""Utility functions for schema handling and import resolution."""

from pathlib import Path
from typing import Dict, Any, Union, List
import yaml
import logging
from importlib import resources
import os

logger = logging.getLogger(__name__)


def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML file safely with advanced import resolution.

    Args:
        file_path: Path to the YAML file to load

    Returns:
        Loaded YAML dictionary
    """
    file_path = Path(file_path)

    try:
        with open(file_path, "r") as f:
            schema = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML file {file_path}: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error reading file {file_path}: {str(e)}")

    return schema


def save_yaml(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """
    Save data to a YAML file.

    Args:
        data: Dictionary to save
        file_path: Path to save the YAML file
    """
    try:
        with open(file_path, "w") as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True)
    except Exception as e:
        raise ValueError(f"Error writing to file {file_path}: {str(e)}")


def resolve_imports(schema: Dict[str, Any], base_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Resolve schema imports with advanced handling.

    Args:
        schema: Schema dictionary
        base_path: Base path for resolving relative imports

    Returns:
        Resolved schema dictionary
    """
    base_path = Path(base_path).parent
    resolved_schema = schema.copy()

    # Special handling for built-in imports
    builtin_imports = {
        "linkml:types": "linkml-runtime/linkml_runtime/linkml/types.yaml",
    }

    if "imports" in schema:
        processed_imports = []
        for import_path in schema["imports"]:
            # Check if it's a built-in import
            if import_path in builtin_imports:
                try:
                    # Try to locate the built-in import
                    import_file = _locate_builtin_import(builtin_imports[import_path])
                    if import_file:
                        imported_schema = load_yaml(import_file)
                        # Merge imported definitions
                        for section in ["classes", "slots", "types", "enums"]:
                            if section in imported_schema:
                                resolved_schema.setdefault(section, {}).update(
                                    imported_schema[section]
                                )
                        processed_imports.append(import_path)
                    else:
                        logger.warning(f"Could not locate built-in import: {import_path}")
                except Exception as e:
                    logger.warning(f"Error processing built-in import {import_path}: {e}")

            # Handle local or absolute file imports
            elif not import_path.startswith("http"):
                try:
                    import_file = base_path / import_path
                    if not import_file.exists():
                        logger.warning(f"Import file not found: {import_file}")
                        continue

                    imported_schema = load_yaml(import_file)
                    # Merge imported definitions
                    for section in ["classes", "slots", "types", "enums"]:
                        if section in imported_schema:
                            resolved_schema.setdefault(section, {}).update(imported_schema[section])
                    processed_imports.append(import_path)
                except Exception as e:
                    logger.warning(f"Error processing import {import_path}: {e}")

            # Skip remote imports for now
            else:
                logger.warning(f"Skipping remote import: {import_path}")

        # Update imports to only include successfully processed imports
        resolved_schema["imports"] = processed_imports

    return resolved_schema


def _locate_builtin_import(relative_path: str) -> Union[str, None]:
    """
    Locate a built-in import file.

    Args:
        relative_path: Relative path to the import file

    Returns:
        Absolute path to the import file or None
    """
    # Try multiple potential locations
    search_paths = [
        # Check in Python package directories
        os.path.join(os.path.dirname(__file__), relative_path),
        os.path.join(os.path.dirname(__file__), "..", relative_path),
        # Check in site-packages
        os.path.join(os.path.dirname(__file__), "site-packages", relative_path),
        # Check in linkml-runtime package
        os.path.join(os.path.dirname(__file__), "linkml-runtime", relative_path),
    ]

    # Try additional package-specific locations
    try:
        import linkml_runtime

        runtime_dir = os.path.dirname(linkml_runtime.__file__)
        search_paths.append(os.path.join(runtime_dir, relative_path))
    except ImportError:
        pass

    # Attempt to find the file
    for path in search_paths:
        if os.path.exists(path):
            return path

    # Fallback: try using importlib resources
    try:
        import importlib.resources as pkg_resources
        import linkml_runtime

        # Try to find the resource
        resource_path = pkg_resources.files(linkml_runtime) / relative_path
        if resource_path.exists():
            return str(resource_path)
    except (ImportError, AttributeError):
        pass

    return None
