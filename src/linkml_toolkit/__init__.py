# File: src/linkml_toolkit/__init__.py
"""LinkML Toolkit - A simple toolkit for working with LinkML schemas."""

from importlib.metadata import version

try:
    __version__ = version("linkml_toolkit")
except Exception:
    __version__ = "unknown"

from .core import LinkMLProcessor
from .validation import SchemaValidator
from .export import SchemaExporter

__all__ = [
    "LinkMLProcessor",
    "SchemaValidator",
    "SchemaExporter",
]
