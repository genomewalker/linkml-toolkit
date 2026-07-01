# File: src/linkml_toolkit/utils.py
"""Utility functions for schema handling and import resolution."""

from pathlib import Path
from typing import Dict, Any, Union, List
import yaml
import logging

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
        with open(file_path, "r", encoding="utf-8") as f:
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
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True)
    except Exception as e:
        raise ValueError(f"Error writing to file {file_path}: {str(e)}")


