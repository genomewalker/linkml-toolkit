# File: src/linkml_toolkit/core.py
"""Core functionality for the LinkML Toolkit."""

from pathlib import Path
from typing import Dict, List, Union, Optional, Any
import logging
import yaml
import sys

from rich.progress import Progress, SpinnerColumn, TextColumn
from collections import OrderedDict
from linkml_runtime.utils.schemaview import SchemaView
from linkml_runtime.linkml_model import SchemaDefinition

from .validation import SchemaValidator
from .utils import load_yaml, save_yaml
from rich.console import Console
from rich.text import Text

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)

console = Console()


class LinkMLProcessor:
    """Process LinkML schemas with support for non-standard fields."""

    def __init__(
        self,
        schema_path: Union[str, Path],
        quiet: bool = False,
        validate: bool = True,
        strict: bool = False,
    ):
        """
        Initialize the processor with a schema file.

        Args:
            schema_path (Union[str, Path]): Path to the schema file
            quiet (bool): Suppress detailed logging
            validate (bool): Validate the schema during processing
            strict (bool): Enable strict error handling
        """
        self.schema_path = Path(schema_path)
        self.quiet = quiet
        self.strict = strict
        self.validator = SchemaValidator(quiet=quiet, strict=strict)
        self.errors = []

        # Load raw schema first
        self.schema_dict = self._load_schema()

        # Create SchemaDefinition
        self.schema = self._create_schema_definition(self.schema_dict)

        if validate:
            self.errors = self.validator.validate_schema(self.schema_path)

        # Initialize SchemaView
        self.schema_view = SchemaView(self.schema)

        if not quiet:
            logger.info(f"Loaded schema from {self.schema_path}")

    def _load_schema(self) -> Dict:
        """
        Load the LinkML schema from file.

        Returns:
            Dict: Loaded schema dictionary
        """
        try:
            with open(self.schema_path) as f:
                schema_dict = yaml.safe_load(f)

            # Validate basic schema structure
            if not isinstance(schema_dict, dict):
                raise ValueError("Schema must be a dictionary")

            # Ensure minimal required fields
            schema_dict.setdefault("name", self.schema_path.stem)
            schema_dict.setdefault("id", f"https://w3id.org/linkml/{schema_dict['name']}")

            # Ensure sections exist
            sections = ["classes", "slots", "types", "enums", "subsets"]
            for section in sections:
                schema_dict.setdefault(section, {})

            return schema_dict

        except Exception as e:
            logger.warning(f"Failed to load schema {self.schema_path}: {e}")
            return {}

    def _create_schema_definition(self, schema_dict: Dict) -> SchemaDefinition:
        """
        Create a SchemaDefinition from schema dictionary.

        Args:
            schema_dict (Dict): Schema dictionary to convert

        Returns:
            SchemaDefinition: Processed schema definition
        """
        if not isinstance(schema_dict, dict):
            raise ValueError("Schema must be a dictionary")

        # Valid properties for SchemaDefinition
        valid_props = {
            "name",
            "id",
            "description",
            "title",
            "version",
            "imports",
            "license",
            "prefixes",
            "default_prefix",
            "default_range",
            "types",
            "enums",
            "slots",
            "classes",
            "metamodel_version",
            "source",
            "see_also",
            "comments",
            "examples",
            "notes",
            "in_subset",
            "from_schema",
            "imported_from",
            "exact_mappings",
            "close_mappings",
            "related_mappings",
            "narrow_mappings",
            "broad_mappings",
            "subsets",
            "settings",
            "annotations",
        }

        # Filter dictionary to only include valid properties
        filtered_dict = {k: v for k, v in schema_dict.items() if k in valid_props}

        try:
            return SchemaDefinition(**filtered_dict)
        except Exception as e:
            if self.strict:
                raise ValueError(f"Error creating SchemaDefinition: {str(e)}")
            # In non-strict mode, create minimal schema
            return SchemaDefinition(name=schema_dict["name"], id=schema_dict["id"])

    def _convert_to_dict(self, obj: Any) -> Dict:
        """Helper method to safely convert objects to dictionaries."""
        if isinstance(obj, dict):
            return dict(obj)
        elif hasattr(obj, "__dict__"):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        elif hasattr(obj, "slots"):
            return {k: getattr(obj, k) for k in obj.__slots__ if hasattr(obj, k)}
        else:
            return {}

    def analyze_schema(self, sections: Optional[List[str]] = None, detailed: bool = False) -> Dict:
        """
        Analyze the schema and return a summary.

        Args:
            sections: List of sections to analyze. Defaults to all sections if None.
            detailed: Whether to provide detailed analysis. Defaults to False.

        Returns:
            Dict: Analysis results of the schema
        """
        if sections is None:
            sections = ["classes", "slots", "enums", "types", "subsets"]

        # Basic metadata with safe attribute access
        results = {
            "name": getattr(self.schema, "name", ""),
            "id": getattr(self.schema, "id", ""),
            "version": getattr(self.schema, "version", "unknown"),
            "description": getattr(self.schema, "description", ""),
            "license": getattr(self.schema, "license", ""),
            "default_prefix": getattr(self.schema, "default_prefix", ""),
        }

        # Handle prefixes
        prefixes = {}
        raw_prefixes = getattr(self.schema, "prefixes", {})
        if isinstance(raw_prefixes, dict):
            prefixes.update(raw_prefixes)
        elif isinstance(raw_prefixes, (list, tuple)):
            for prefix in raw_prefixes:
                if isinstance(prefix, dict):
                    prefixes.update(prefix)
                else:
                    prefix_dict = self._convert_to_dict(prefix)
                    if "prefix_prefix" in prefix_dict and "prefix_reference" in prefix_dict:
                        prefixes[prefix_dict["prefix_prefix"]] = prefix_dict["prefix_reference"]
        results["prefixes"] = prefixes

        # Analyze requested sections
        for section in sections:
            if section == "classes":
                results[section] = self._analyze_classes(detailed)
            elif section == "slots":
                results[section] = self._analyze_slots(detailed)
            elif section == "enums":
                results[section] = self._analyze_enums(detailed)
            elif section == "types":
                results[section] = self._analyze_types(detailed)
            elif section == "subsets":
                results[section] = self._analyze_subsets(detailed)

        return results

    def _analyze_classes(self, detailed: bool = False) -> Dict:
        """Analyze classes in the schema."""
        classes = {}
        for class_name in self.schema_view.all_classes():
            try:
                class_def = self.schema_view.get_class(class_name)
                if detailed:
                    class_info = self.analyze_class(class_name)
                    if class_info:
                        classes[class_name] = class_info
                else:
                    # Provide minimal info instead of just True
                    classes[class_name] = {
                        "name": class_name,
                        "description": getattr(class_def, "description", ""),
                        "abstract": getattr(class_def, "abstract", False),
                        "slots": getattr(class_def, "slots", []),
                        "is_a": getattr(class_def, "is_a", ""),
                        "mixins": getattr(class_def, "mixins", []),
                    }
            except Exception as e:
                logger.warning(f"Error analyzing class {class_name}: {str(e)}")
                classes[class_name] = {"name": class_name, "description": "Error analyzing class"}
        return classes

    def _analyze_slots(self, detailed: bool = False) -> Dict:
        """Analyze slots in the schema."""
        slots = {}
        for slot_name in self.schema_view.all_slots():
            try:
                slot_def = self.schema_view.get_slot(slot_name)
                if detailed:
                    slot_info = self.analyze_slot(slot_name)
                    if slot_info:
                        slots[slot_name] = slot_info
                else:
                    # Provide minimal info instead of just True
                    slots[slot_name] = {
                        "name": slot_name,
                        "description": getattr(slot_def, "description", ""),
                        "range": getattr(slot_def, "range", ""),
                        "required": getattr(slot_def, "required", False),
                        "multivalued": getattr(slot_def, "multivalued", False),
                        "domain": getattr(slot_def, "domain", ""),
                    }
            except Exception as e:
                logger.warning(f"Error analyzing slot {slot_name}: {str(e)}")
                slots[slot_name] = {"name": slot_name, "description": "Error analyzing slot"}
        return slots

    def _analyze_enums(self, detailed: bool = False) -> Dict:
        """Analyze enums in the schema."""
        enums = {}
        for enum_name in self.schema_view.all_enums():
            try:
                enum_def = self.schema_view.get_enum(enum_name)
                if detailed:
                    enum_info = self.analyze_enum(enum_name)
                    if enum_info:
                        enums[enum_name] = enum_info
                else:
                    # Provide minimal info instead of just True
                    enums[enum_name] = {
                        "name": enum_name,
                        "description": getattr(enum_def, "description", ""),
                        "permissible_values": getattr(enum_def, "permissible_values", {}),
                    }
            except Exception as e:
                logger.warning(f"Error analyzing enum {enum_name}: {str(e)}")
                enums[enum_name] = {"name": enum_name, "description": "Error analyzing enum"}
        return enums

    def _analyze_types(self, detailed: bool = False) -> Dict:
        """Analyze types in the schema."""
        types = {}
        for type_name in self.schema_view.all_types():
            try:
                type_def = self.schema_view.get_type(type_name)
                if detailed:
                    types[type_name] = {
                        "name": type_name,
                        "description": getattr(type_def, "description", ""),
                        "typeof": getattr(type_def, "typeof", ""),
                        "uri": getattr(type_def, "uri", ""),
                    }
                else:
                    # Provide minimal info instead of just True
                    types[type_name] = {
                        "name": type_name,
                        "description": getattr(type_def, "description", ""),
                        "typeof": getattr(type_def, "typeof", ""),
                    }
            except Exception as e:
                logger.warning(f"Error analyzing type {type_name}: {str(e)}")
                types[type_name] = {"name": type_name, "description": "Error analyzing type"}
        return types

    def _analyze_subsets(self, detailed: bool = False) -> Dict:
        """Analyze subsets in the schema."""
        subsets = {}
        raw_subsets = getattr(self.schema, "subsets", {})

        try:
            if isinstance(raw_subsets, dict):
                for name, subset in raw_subsets.items():
                    if detailed:
                        subsets[name] = self._convert_to_dict(subset)
                    else:
                        subsets[name] = True
            elif isinstance(raw_subsets, (list, tuple)):
                for subset in raw_subsets:
                    subset_dict = self._convert_to_dict(subset)
                    if "name" in subset_dict:
                        name = subset_dict["name"]
                        if detailed:
                            subsets[name] = subset_dict
                        else:
                            subsets[name] = True
        except Exception as e:
            logger.warning(f"Error analyzing subsets: {str(e)}")

        return subsets

    def analyze_class(self, class_name: str, include_inherited: bool = True) -> Optional[Dict]:
        """
        Analyze a specific class.

        Args:
            class_name (str): Name of the class to analyze
            include_inherited (bool, optional): Include inherited slots. Defaults to True.

        Returns:
            Optional[Dict]: Detailed analysis of the class, or None if class not found
        """
        class_def = self.schema_view.get_class(class_name)
        if not class_def:
            return None

        result = {
            "name": class_name,
            "description": getattr(class_def, "description", ""),
            "slots": {},
            "is_a": getattr(class_def, "is_a", ""),
            "mixins": getattr(class_def, "mixins", []),
            "abstract": getattr(class_def, "abstract", False),
        }

        # Get all slots including inherited if requested
        if include_inherited:
            slots = self.schema_view.class_slots(class_name)
        else:
            slots = class_def.slots or []

        for slot_name in slots:
            slot_def = self.schema_view.get_slot(slot_name)
            if slot_def:
                result["slots"][slot_name] = {
                    "description": getattr(slot_def, "description", ""),
                    "range": getattr(slot_def, "range", ""),
                    "required": getattr(slot_def, "required", False),
                    "multivalued": getattr(slot_def, "multivalued", False),
                    "inherited": slot_name not in (class_def.slots or []),
                }

        return result

    def analyze_slot(self, slot_name: str) -> Optional[Dict]:
        """
        Analyze a specific slot dynamically.

        Args:
            slot_name (str): Name of the slot to analyze

        Returns:
            Optional[Dict]: Detailed analysis of the slot, or None if slot not found
        """
        slot_def = self.schema_view.get_slot(slot_name)
        if not slot_def:
            return None

        def safe_convert(obj):
            """Safely convert any object to a JSON-serializable format."""
            if obj is None:
                return None
            elif isinstance(obj, (str, int, float, bool)):
                return obj
            elif isinstance(obj, (list, tuple)):
                return [safe_convert(x) for x in obj]
            elif isinstance(obj, dict):
                return {str(k): safe_convert(v) for k, v in obj.items()}
            elif hasattr(obj, "to_dict"):
                return safe_convert(obj.to_dict())
            elif hasattr(obj, "__dict__"):
                return {
                    k: safe_convert(v) for k, v in obj.__dict__.items() if not k.startswith("_")
                }
            else:
                return str(obj)

        # Get all attributes dynamically
        analysis = {}
        for attr in dir(slot_def):
            if not attr.startswith("_"):  # Skip private attributes
                try:
                    value = getattr(slot_def, attr)
                    if callable(value):  # Skip methods
                        continue
                    analysis[attr] = safe_convert(value)
                except Exception as e:
                    logger.debug(f"Error converting attribute {attr}: {str(e)}")

        # Add usage information
        usage = {}
        try:
            for class_name in self.schema_view.all_classes():
                class_def = self.schema_view.get_class(class_name)
                if not class_def:
                    continue

                class_slots = getattr(class_def, "slots", []) or []
                inherited_slots = self.schema_view.class_induced_slots(class_name)

                if slot_name in class_slots or slot_name in inherited_slots:
                    is_direct = slot_name in class_slots
                    class_info = {
                        "own": is_direct,
                        "inherited": not is_direct,
                    }

                    # Add slot usage if present
                    if hasattr(class_def, "slot_usage"):
                        slot_usage = getattr(class_def, "slot_usage", {}).get(slot_name)
                        if slot_usage:
                            # Extract specific keys from slot_usage
                            overrides = slot_usage.get("overrides")
                            required = slot_usage.get("required")
                            multivalued = slot_usage.get("multivalued")

                            # Add extracted information to class_info
                            if overrides is not None:
                                class_info["overrides"] = overrides
                            if required is not None:
                                class_info["required"] = required
                            if multivalued is not None:
                                class_info["multivalued"] = multivalued

                    usage[class_name] = class_info

        except Exception as e:
            logger.debug(f"Error analyzing slot usage: {str(e)}")

        analysis["usage"] = usage
        return analysis

    def analyze_enum(self, enum_name: str) -> Optional[Dict]:
        """
        Analyze a specific enum.

        Args:
            enum_name (str): Name of the enum to analyze

        Returns:
            Optional[Dict]: Detailed analysis of the enum, or None if enum not found
        """
        enum_def = self.schema_view.get_enum(enum_name)
        if not enum_def:
            return None

        return {
            "name": enum_name,
            "description": getattr(enum_def, "description", ""),
            "permissible_values": getattr(enum_def, "permissible_values", {}),
        }

    def _get_slot_usage(self, slot_name: str) -> Dict:
        """
        Get usage information for a slot across different classes.

        Args:
            slot_name (str): Name of the slot to analyze

        Returns:
            Dict: Usage information for the slot
        """
        usage = {}
        try:
            for class_name in self.schema_view.all_classes():
                class_def = self.schema_view.get_class(class_name)
                class_slots = self.schema_view.class_slots(class_name)

                if not class_slots:
                    continue

                if slot_name in class_slots:
                    # Get slot usage from the class definition
                    slot_usage = {}
                    if hasattr(class_def, "slot_usage") and class_def.slot_usage:
                        slot_usage = getattr(
                            class_def.slot_usage.get(slot_name, {}), "attributes", {}
                        )

                    # Check if slot is directly in class slots
                    is_direct = slot_name in (class_def.slots or [])

                    usage[class_name] = {
                        "required": slot_usage.get("required", False),
                        "own": is_direct,
                        "inherited": not is_direct,
                    }

                    # Add any slot usage overrides
                    if slot_usage:
                        usage[class_name]["overrides"] = dict(slot_usage)
        except Exception as e:
            logger.warning(f"Error getting slot usage for {slot_name}: {str(e)}")

        return usage

    def save(self, schema: Dict, output_path: Union[str, Path]):
        """
        Save the schema to a file.

        Args:
            schema (Dict): Schema dictionary to save
            output_path (Union[str, Path]): Path to save the schema
        """
        save_yaml(schema, output_path)
        if not self.quiet:
            logger.info(f"Saved schema to {output_path}")

    @classmethod
    def _load_schema_list(cls, schema_list: str, input_type: str = "auto") -> List[Path]:
        """
        Load a list of schemas from either a comma-separated string or a file.

        Args:
            schema_list (str): String of schema paths or file containing schema paths
            input_type (str): Method of interpreting input

        Returns:
            List[Path]: List of schema file paths

        Raises:
            ValueError: If no valid schema paths are found
            FileNotFoundError: If the schema list file is not found
        """
        # Validate input type
        valid_input_types = ["auto", "file", "list"]
        if input_type not in valid_input_types:
            raise ValueError(
                f"Invalid input_type: {input_type}. Must be one of {valid_input_types}"
            )

        # Determine input method
        is_file_input = input_type == "file" or (input_type == "auto" and not "," in schema_list)

        try:
            if is_file_input:
                # Attempt to load from file
                list_path = Path(schema_list)

                # Validate file exists
                if not list_path.is_file():
                    raise FileNotFoundError(f"Schema list file not found: {schema_list}")

                # Read paths from file
                with open(list_path) as f:
                    paths = [
                        Path(line.strip())
                        for line in f
                        if line.strip() and not line.startswith("#")
                    ]

                # Validate paths were found
                if not paths:
                    raise ValueError(f"No valid schema paths found in file: {schema_list}")

                return paths

            # Treat as comma-separated list
            paths = [Path(s.strip()) for s in schema_list.split(",") if s.strip()]

            # Validate paths were found
            if not paths:
                raise ValueError("No valid schema paths found in comma-separated list")

            return paths

        except (FileNotFoundError, ValueError) as e:
            # Log the specific error
            logger.error(f"Error loading schema list: {e}")
            raise

        except Exception as e:
            # Catch any unexpected errors
            logger.error(f"Unexpected error loading schema list: {e}")
            raise ValueError(f"Failed to load schema list: {e}")

    @classmethod
    def merge_multiple(
        cls,
        schema_list: str,
        input_type: str = "auto",
        validate: bool = True,
        strict: bool = False,
        return_errors: bool = True,
    ) -> Dict:
        """
        Merge multiple schemas while preserving structure of the first schema.

        Args:
            schema_list: List of schema paths or file containing schema paths
            input_type: Method of interpreting input
            validate: Whether to validate schemas during processing
            strict: Enable strict error handling

        Returns:
            Dict containing merged schema maintaining original structure
        """
        # Load schema paths
        paths = cls._load_schema_list(schema_list, input_type)

        if len(paths) < 2:
            raise ValueError("At least two schemas are required for merging")
        # Process and merge schemas
        processed_schemas = []
        errors = {}
        for path in paths:
            try:
                processor = cls(path, validate=validate, strict=strict)
                if processor.schema_dict:
                    processed_schemas.append(processor)
                else:
                    logger.warning(f"Skipping empty schema: {path}")
                if processor.errors:
                    errors[str(path)] = processor.errors
            except Exception as e:
                logger.error(f"Failed to process schema {path}: {e}")
                if strict:
                    raise

        if len(processed_schemas) < 2:
            raise ValueError("Not enough valid schemas to merge")

        # Use first schema as base and analyze its structure
        base_processor = processed_schemas[0]
        base_structure = base_processor.analyze_schema_structure()

        # Start with a deep copy of the base schema
        merged = OrderedDict()

        # Copy all sections following original order
        for section in base_structure["order"]:
            if section in base_processor.schema_dict:
                if section not in ["classes", "slots", "types", "enums", "subsets"]:
                    # Copy metadata sections exactly
                    value = base_processor.schema_dict[section]
                    if isinstance(value, dict):
                        merged[section] = OrderedDict(value)
                    else:
                        merged[section] = value
                else:
                    # Initialize mergeable sections
                    merged[section] = OrderedDict()
                    if section in base_processor.schema_dict:
                        merged[section].update(base_processor.schema_dict[section])

        # Merge content from other schemas
        for other_processor in processed_schemas[1:]:
            # Handle metadata fields - only merge lists/dicts
            for section in base_structure["order"]:
                if section not in ["classes", "slots", "types", "enums", "subsets"]:
                    if section in other_processor.schema_dict:
                        if isinstance(merged.get(section), list) and isinstance(
                            other_processor.schema_dict[section], list
                        ):
                            # Merge lists uniquely
                            merged[section] = list(
                                set(merged[section] + other_processor.schema_dict[section])
                            )
                        elif isinstance(merged.get(section), dict) and isinstance(
                            other_processor.schema_dict[section], dict
                        ):
                            # Update dicts
                            merged[section].update(other_processor.schema_dict[section])

            # Merge main sections
            for section in ["classes", "slots", "types", "enums"]:
                if section in other_processor.schema_dict:
                    # Add new items from other schema
                    for key, value in other_processor.schema_dict[section].items():
                        if key in merged[section]:
                            # Merge existing items
                            if isinstance(value, dict) and isinstance(merged[section][key], dict):
                                merged[section][key].update(value)
                        else:
                            # Add new items
                            merged[section][key] = value

            # Handle subsets specially - preserve empty subset structure
            if "subsets" in other_processor.schema_dict:
                for key, value in other_processor.schema_dict["subsets"].items():
                    if key not in merged["subsets"]:
                        # Use the same empty value format as the base schema
                        empty_format = (
                            base_structure["empty_values"]
                            .get("subsets", {})
                            .get(next(iter(base_processor.schema_dict.get("subsets", {})), None))
                        )
                        merged["subsets"][key] = empty_format

        if return_errors:
            return merged, errors
        return merged

    @classmethod
    def concat_multiple(
        cls, schema_list: str, input_type: str = "auto", validate: bool = True, strict: bool = False
    ) -> Dict:
        """
        Concatenate multiple schemas while preserving structure of the first schema.

        Args:
            schema_list: List of schema paths or file containing schema paths
            input_type: Method of interpreting input
            validate: Whether to validate schemas during processing
            strict: Enable strict error handling

        Returns:
            Dict containing concatenated schema maintaining original structure
        """
        # Load schema paths
        paths = cls._load_schema_list(schema_list, input_type)

        if len(paths) < 2:
            raise ValueError("At least two schemas are required for concatenation")

        # Process schemas
        processed_schemas = []
        for path in paths:
            try:
                processor = cls(path, validate=validate, strict=strict)
                if processor.schema_dict:
                    processed_schemas.append(processor)
                else:
                    logger.warning(f"Skipping empty schema: {path}")
            except Exception as e:
                logger.error(f"Failed to process schema {path}: {e}")
                if strict:
                    raise

        if len(processed_schemas) < 2:
            raise ValueError("Not enough valid schemas to concatenate")

        # Use first schema as base and analyze its structure
        base_processor = processed_schemas[0]
        base_structure = base_processor.analyze_schema_structure()

        # Start with base schema structure
        concatenated = OrderedDict()

        # Copy all sections following original order
        for section in base_structure["order"]:
            if section in base_processor.schema_dict:
                if section not in ["classes", "slots", "types", "enums", "subsets"]:
                    # Copy metadata sections exactly
                    value = base_processor.schema_dict[section]
                    if isinstance(value, dict):
                        concatenated[section] = OrderedDict(value)
                    else:
                        concatenated[section] = value
                else:
                    # Initialize concatenable sections
                    concatenated[section] = OrderedDict()
                    if section in base_processor.schema_dict:
                        concatenated[section].update(base_processor.schema_dict[section])

        # Process remaining schemas
        for i, other_processor in enumerate(processed_schemas[1:], start=1):
            path_stem = Path(paths[i]).stem

            # Handle main sections
            for section in ["classes", "slots", "types", "enums"]:
                if section in other_processor.schema_dict:
                    for key, value in other_processor.schema_dict[section].items():
                        # Create unique key if name conflicts
                        new_key = f"{key}_{path_stem}" if key in concatenated[section] else key
                        concatenated[section][new_key] = value

            # Handle subsets specially
            if "subsets" in other_processor.schema_dict:
                for key in other_processor.schema_dict["subsets"]:
                    new_key = f"{key}_{path_stem}" if key in concatenated["subsets"] else key
                    # Use the same empty value format as the base schema
                    empty_format = (
                        base_structure["empty_values"]
                        .get("subsets", {})
                        .get(next(iter(base_processor.schema_dict.get("subsets", {})), None))
                    )
                    concatenated["subsets"][new_key] = empty_format

        return concatenated

    def analyze_schema_structure(self) -> Dict:
        """
        Analyze the structure of the original schema to use as a template.

        Returns:
            Dict containing metadata about the schema structure including:
            - order of sections
            - format of values (null vs empty)
            - indentation and formatting patterns
        """
        structure = {
            "order": list(self.schema_dict.keys()),
            "empty_values": {},
            "section_formats": {},
        }

        # Analyze how empty values are represented in each section
        for section, content in self.schema_dict.items():
            if isinstance(content, dict):
                empty_format = {}
                for key, value in content.items():
                    if value is None or value == "" or (isinstance(value, dict) and not value):
                        empty_format[key] = value
                structure["empty_values"][section] = empty_format

            # Record section format (dict, list, etc)
            structure["section_formats"][section] = type(content)

        return structure

    def subset_by_class(self, class_names: List[str], include_inherited: bool = True) -> Dict:
        """
        Create a subset of the schema containing only specified classes and their dependencies,
        while preserving the original schema structure and metadata.
        """
        # First analyze the original schema structure
        original_structure = self.analyze_schema_structure()

        # Create new dict following original order
        subsetted = OrderedDict()

        # Track required components
        required_classes = set()
        required_slots = set()
        required_types = set()
        required_enums = set()
        required_subsets = set()

        def add_class_and_deps(class_name: str):
            if class_name not in self.schema_view.all_classes():
                return

            class_def = self.schema_view.get_class(class_name)
            required_classes.add(class_name)

            # Track subsets used by the class
            if hasattr(class_def, "in_subset"):
                if isinstance(class_def.in_subset, list):
                    required_subsets.update(class_def.in_subset)
                elif class_def.in_subset:
                    required_subsets.add(class_def.in_subset)

            # Add parent class if inheritance is included
            if include_inherited and class_def.is_a:
                add_class_and_deps(class_def.is_a)

            # Add mixin classes
            if include_inherited and class_def.mixins:
                for mixin in class_def.mixins:
                    add_class_and_deps(mixin)

            # Add slots used by the class
            slots = self.schema_view.class_slots(class_name)
            for slot_name in slots:
                slot_def = self.schema_view.get_slot(slot_name)
                if slot_def:
                    required_slots.add(slot_name)

                    # Track subsets used by the slot
                    if hasattr(slot_def, "in_subset"):
                        if isinstance(slot_def.in_subset, list):
                            required_subsets.update(slot_def.in_subset)
                        elif slot_def.in_subset:
                            required_subsets.add(slot_def.in_subset)

                    # Add slot range dependencies
                    if slot_def.range:
                        if slot_def.range in self.schema_view.all_classes():
                            add_class_and_deps(slot_def.range)
                        elif slot_def.range in self.schema_view.all_types():
                            required_types.add(slot_def.range)
                        elif slot_def.range in self.schema_view.all_enums():
                            required_enums.add(slot_def.range)

        # Process requested classes
        for class_name in class_names:
            add_class_and_deps(class_name)

        # Follow original schema order and formats
        for section in original_structure["order"]:
            original_content = self.schema_dict.get(section, {})

            if section == "subsets":
                # Preserve all original subsets with their original empty value format
                if "subsets" in self.schema_dict:
                    subsetted["subsets"] = OrderedDict()
                    for k, v in self.schema_dict["subsets"].items():
                        # Use original empty value format
                        empty_format = original_structure["empty_values"].get("subsets", {}).get(k)
                        subsetted["subsets"][k] = empty_format

            elif section == "classes" and required_classes:
                subsetted["classes"] = OrderedDict(
                    (k, dict(v) if isinstance(v, dict) else v)
                    for k, v in original_content.items()
                    if k in required_classes
                )

            elif section == "slots" and required_slots:
                subsetted["slots"] = OrderedDict(
                    (k, dict(v) if isinstance(v, dict) else v)
                    for k, v in original_content.items()
                    if k in required_slots
                )

            elif section == "types":
                # Handle both imported and required types
                subsetted["types"] = OrderedDict()
                for k, v in original_content.items():
                    if (
                        isinstance(v, dict)
                        and v.get("from_schema") == "https://w3id.org/linkml/types"
                    ) or k in required_types:
                        subsetted["types"][k] = dict(v) if isinstance(v, dict) else v

            elif section == "enums" and required_enums:
                subsetted["enums"] = OrderedDict(
                    (k, dict(v) if isinstance(v, dict) else v)
                    for k, v in original_content.items()
                    if k in required_enums
                )
            else:
                # Copy other sections exactly as they are
                if section in self.schema_dict:
                    value = self.schema_dict[section]
                    if isinstance(value, dict):
                        subsetted[section] = OrderedDict(value)
                    else:
                        subsetted[section] = value

        # Add subsetting note to description
        if "description" in subsetted:
            desc = subsetted["description"]
            if not isinstance(desc, str):
                desc = str(desc)

            # Remove any existing lines about being a subset
            desc_lines = [
                line for line in desc.split("\n") if "subset of the original schema" not in line
            ]

            # Add new subset description line
            subset_line = f"This is a subset of the original schema containing the following classes: {', '.join(sorted(class_names))}."

            # Ensure no duplicates are added
            if subset_line not in desc_lines:
                if not desc.endswith("\n"):
                    desc_lines.append("")
                desc_lines.append(subset_line)

            subsetted["description"] = "\n".join(desc_lines).strip()

        return subsetted

    def generate_class_hierarchy_text(self) -> str:
        """
        Generate a text-based representation of the class hierarchy.

        Returns:
            str: Text representation of class hierarchy
        """
        # Prepare class hierarchy
        hierarchy = {}
        for class_name, class_def in self.schema_view.all_classes().items():
            parent = getattr(class_def, "is_a", None)

            if parent not in hierarchy:
                hierarchy[parent] = []
            hierarchy.setdefault(parent, []).append(class_name)

        def generate_tree(parent=None, indent=""):
            tree_lines = []
            children = hierarchy.get(parent, [])

            for i, child in enumerate(sorted(children)):
                # Determine class type annotations
                class_def = self.schema_view.get_class(child)
                type_annotation = ""
                if getattr(class_def, "mixin", False):
                    type_annotation = " (Mixin)"
                elif getattr(class_def, "abstract", False):
                    type_annotation = " (Abstract)"

                # Last child uses different tree connection
                if i == len(children) - 1:
                    tree_lines.append(f"{indent}└── {child}{type_annotation}")
                    child_indent = indent + "    "
                else:
                    tree_lines.append(f"{indent}├── {child}{type_annotation}")
                    child_indent = indent + "│   "

                # Recursively generate subtree
                tree_lines.extend(generate_tree(child, child_indent))

            return tree_lines

        # Generate full hierarchy starting from root classes (no parent)
        full_tree_lines = []
        root_classes = [
            cls
            for cls, class_def in self.schema_view.all_classes().items()
            if not getattr(class_def, "is_a", None)
        ]

        for root in sorted(root_classes):
            full_tree_lines.append(f"{root}")
            full_tree_lines.extend(generate_tree(root))
            full_tree_lines.append("")  # Separator between root trees

        return "\n".join(full_tree_lines)

    def save_class_hierarchy_diagram(self, output_path: Union[str, Path]):
        """
        Generate a text-based class hierarchy diagram.

        Args:
            output_path (Union[str, Path]): Path to save the diagram
        """
        output_path = Path(output_path)

        # Prepare class hierarchy
        hierarchy = {}
        for class_name, class_def in self.schema_view.all_classes().items():
            parent = getattr(class_def, "is_a", None)

            if parent not in hierarchy:
                hierarchy[parent] = []
            hierarchy.setdefault(parent, []).append(class_name)

        def generate_tree(parent=None, indent=""):
            tree_lines = []
            children = hierarchy.get(parent, [])

            for i, child in enumerate(sorted(children)):
                # Determine class type annotations
                class_def = self.schema_view.get_class(child)
                type_annotation = ""
                if getattr(class_def, "mixin", False):
                    type_annotation = " (Mixin)"
                elif getattr(class_def, "abstract", False):
                    type_annotation = " (Abstract)"

                # Last child uses different tree connection
                if i == len(children) - 1:
                    tree_lines.append(f"{indent}└── {child}{type_annotation}")
                    child_indent = indent + "    "
                else:
                    tree_lines.append(f"{indent}├── {child}{type_annotation}")
                    child_indent = indent + "│   "

                # Recursively generate subtree
                tree_lines.extend(generate_tree(child, child_indent))

            return tree_lines

        # Generate full hierarchy starting from root classes (no parent)
        full_tree_lines = []
        root_classes = [
            cls
            for cls, class_def in self.schema_view.all_classes().items()
            if not getattr(class_def, "is_a", None)
        ]

        for root in sorted(root_classes):
            full_tree_lines.append(f"{root}")
            full_tree_lines.extend(generate_tree(root))
            full_tree_lines.append("")  # Separator between root trees

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(output_path, "w") as f:
            f.write("\n".join(full_tree_lines))

    def save_class_diagram(self, class_name: str, output_path: Union[str, Path]):
        """
        Generate a text-based detailed diagram for a specific class.

        Args:
            class_name (str): Name of the class to diagram
            output_path (Union[str, Path]): Path to save the diagram

        Raises:
            ValueError: If specified class does not exist
        """
        # Verify class exists
        class_def = self.schema_view.get_class(class_name)
        if not class_def:
            raise ValueError(f"Class '{class_name}' not found in schema")

        # Prepare class details
        details = [
            f"Class: {class_name}",
            f"Description: {getattr(class_def, 'description', 'No description available')}",
        ]

        # Add class type information
        if getattr(class_def, "abstract", False):
            details.append("Type: Abstract Class")
        elif getattr(class_def, "mixin", False):
            details.append("Type: Mixin Class")

        # Add inheritance information
        parent = getattr(class_def, "is_a", None)
        if parent:
            details.append(f"Inherits from: {parent}")

        # Add mixins
        mixins = getattr(class_def, "mixins", [])
        if mixins:
            details.append(f"Mixins: {', '.join(mixins)}")

        # Add slots
        details.append("\nSlots:")
        for slot_name in self.schema_view.class_slots(class_name):
            slot_def = self.schema_view.get_slot(slot_name)

            # Prepare slot details
            slot_info = [slot_name]

            # Add range
            range_info = slot_def.range or "Any"
            slot_info.append(f"  Range: {range_info}")

            # Add constraints
            constraints = []
            if slot_def.required:
                constraints.append("required")
            if slot_def.multivalued:
                constraints.append("multivalued")

            if constraints:
                slot_info.append(f"  Constraints: {', '.join(constraints)}")

            # Add description if available
            if slot_def.description:
                slot_info.append(f"  Description: {slot_def.description}")

            details.extend(slot_info)
            details.append("")  # Empty line between slots

        # Ensure parent directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(output_path, "w") as f:
            f.write("\n".join(details))

    def subset_schema(self, class_names: List[str], include_inherited: bool = True) -> Dict:
        """
        Create a subset of the schema containing only specified classes and their dependencies.

        Args:
            class_names (List[str]): List of class names to include in the subset
            include_inherited (bool, optional): Include inherited slots and parent classes. Defaults to True.

        Returns:
            Dict: Subset of the original schema

        Raises:
            ValueError: If no valid classes are found
        """
        # Validate input classes
        valid_classes = [cls for cls in class_names if cls in self.schema_view.all_classes()]

        if not valid_classes:
            raise ValueError(f"No valid classes found. Specified classes: {class_names}")

        # Create subset using analyze_schema_structure and subset logic
        subsetted = self.subset_by_class(valid_classes, include_inherited)

        # Update description to indicate this is a subset
        # When adding the subset description
        if "description" in subsetted:
            desc = subsetted["description"]
            if not isinstance(desc, str):
                desc = str(desc)

            # Remove any existing lines about being a subset
            desc_lines = [
                line for line in desc.split("\n") if "subset of the original schema" not in line
            ]

            # Add new subset description line
            subset_line = f"This is a subset of the original schema containing the following classes: {', '.join(sorted(class_names))}."

            # Ensure no duplicates are added
            if subset_line not in desc_lines:
                if not desc.endswith("\n"):
                    desc_lines.append("")
                desc_lines.append(subset_line)

            subsetted["description"] = "\n".join(desc_lines).strip()

        return subsetted


def save_yaml(data: Dict, path: Union[str, Path]) -> None:
    """
    Save a dictionary to a YAML file while preserving structure and empty values.

    Args:
        data: Dictionary to save
        path: Path to save the YAML file
    """

    class StructurePreservingDumper(yaml.Dumper):
        """Custom YAML dumper that preserves structure and empty values."""

        def represent_none(self, _):
            """Represent None as empty string."""
            return self.represent_scalar("tag:yaml.org,2002:null", "")

        def represent_dict(self, data):
            """Preserve order of dictionary items."""
            return self.represent_mapping("tag:yaml.org,2002:map", data.items())

        def represent_str(self, data):
            """Handle string serialization with proper quotation."""
            style = None
            if "\n" in data:  # Use literal block for multiline
                style = "|"
            elif ":" in data or "#" in data:  # Quote strings containing special characters
                style = '"'
            return self.represent_scalar("tag:yaml.org,2002:str", data, style=style)

    # Register representers
    StructurePreservingDumper.add_representer(type(None), StructurePreservingDumper.represent_none)
    StructurePreservingDumper.add_representer(OrderedDict, StructurePreservingDumper.represent_dict)
    StructurePreservingDumper.add_representer(dict, StructurePreservingDumper.represent_dict)
    StructurePreservingDumper.add_representer(str, StructurePreservingDumper.represent_str)

    # Ensure path parent exists
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Save with custom dumper
    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                Dumper=StructurePreservingDumper,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                width=float("inf"),  # Prevent line wrapping
            )
    except Exception as e:
        logger.error(f"Error saving YAML to {path}: {e}")
        raise
