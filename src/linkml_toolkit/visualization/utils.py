# File: src/linkml_toolkit/visualization/utils.py
"""Utility functions for visualization."""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json


def prepare_visualization_data(processor) -> Dict:
    """Prepare comprehensive data for visualization."""
    # Process metadata
    metadata = {
        "name": processor.schema.name,
        "version": getattr(processor.schema, "version", "Unknown"),
        "description": getattr(processor.schema, "description", ""),
        "license": getattr(processor.schema, "license", ""),
        "prefixes": getattr(processor.schema, "prefixes", {}),
    }

    # Process structure elements with full details
    structure = {
        "classes": prepare_class_data(processor),
        "slots": prepare_slot_data(processor),
        "enums": prepare_enum_data(processor),
        "types": prepare_type_data(processor),
    }
    # Process relationships
    relationships = {
        "hierarchy": prepare_hierarchy_data(processor),
        "dependencies": prepare_dependency_data(processor),
    }

    return {
        "metadata": metadata,
        "structure": structure,
        "relationships": relationships,
    }


def prepare_slot_data(processor) -> Dict[str, Dict]:
    """Prepare comprehensive slot data for visualization."""
    slots = {}
    for slot_name in processor.schema_view.all_slots():
        slot_def = processor.schema_view.get_slot(slot_name)
        if slot_def:
            # Get all possible attributes
            slot_data = {}
            for attr in dir(slot_def):
                if not attr.startswith("_"):  # Skip private attributes
                    value = getattr(slot_def, attr)
                    if not callable(value):  # Skip methods
                        slot_data[attr] = value

            # Add relationships data
            usage_info = {}
            for class_name, class_def in processor.schema_view.all_classes().items():
                induced_slots = processor.schema_view.class_induced_slots(class_name)
                if slot_name in induced_slots:
                    usage_info[class_name] = {
                        "inherited": slot_name not in getattr(class_def, "slots", []),
                        "required": getattr(slot_def, "required", False),
                        "from_class": class_name,
                    }

            slot_data["usage_in_classes"] = usage_info
            slots[slot_name] = slot_data

    return slots


def prepare_enum_data(processor) -> Dict[str, Dict]:
    """Prepare comprehensive enum data for visualization."""
    enums = {}
    for enum_name in processor.schema_view.all_enums():
        enum_def = processor.schema_view.get_enum(enum_name)
        if enum_def:
            # Process permissible values
            processed_values = {}
            for value_name, value_obj in getattr(enum_def, "permissible_values", {}).items():
                processed_values[value_name] = {
                    "text": value_name,  # Use value_name as the text
                    "description": value_obj.description,
                    "meaning": value_obj.meaning,
                }

            # Find used slots
            used_in_slots = []
            for slot_name, slot_def in processor.schema_view.all_slots().items():
                if getattr(slot_def, "range", None) == enum_name:
                    used_in_slots.append(slot_name)

            enum_data = {
                "name": enum_name,
                "description": getattr(enum_def, "description", ""),
                "permissible_values": processed_values,
                "used_in_slots": used_in_slots,
            }

            enums[enum_name] = enum_data

    return enums


def prepare_class_data(processor) -> Dict[str, Dict]:
    """Prepare class data for visualization."""
    classes = {}
    for class_name in processor.schema_view.all_classes():
        class_def = processor.schema_view.get_class(class_name)
        if class_def:
            slots_info = {}
            for slot_name in getattr(class_def, "slots", []):
                slot_def = processor.schema_view.get_slot(slot_name)
                if slot_def:
                    slots_info[slot_name] = {
                        "description": getattr(slot_def, "description", ""),
                        "range": getattr(slot_def, "range", ""),
                        "required": getattr(slot_def, "required", False),
                        "multivalued": getattr(slot_def, "multivalued", False),
                        "examples": getattr(slot_def, "examples", []),
                    }

            class_data = {
                "name": class_name,
                "description": getattr(class_def, "description", ""),
                "slots": slots_info,
                "is_a": getattr(class_def, "is_a", ""),
                "mixins": getattr(class_def, "mixins", []),
                "abstract": getattr(class_def, "abstract", False),
                "title": getattr(class_def, "title", ""),
                "comments": getattr(class_def, "comments", []),
                "class_uri": getattr(class_def, "class_uri", ""),
                "slot_usage": getattr(class_def, "slot_usage", {}),
            }
            classes[class_name] = class_data
    return classes


def prepare_type_data(processor) -> Dict[str, Dict]:
    """Prepare type data for visualization."""
    types = {}
    for type_name in processor.schema_view.all_types():
        type_def = processor.schema_view.get_type(type_name)
        if type_def:
            types[type_name] = {
                "name": type_name,
                "description": getattr(type_def, "description", ""),
                "typeof": getattr(type_def, "typeof", ""),
                "uri": getattr(type_def, "uri", ""),
            }
    return types


def prepare_slot_usage_info(processor, slot_name: str) -> Dict:
    """
    Prepare usage information for a slot, handling missing references gracefully.
    If a slot references a missing domain or range, it will be skipped rather than causing an error.
    Prepare detailed usage information for a slot.
    """
    usage = {}
    for class_name in processor.schema_view.all_classes():
        class_def = processor.schema_view.get_class(class_name)
        if not class_def:
            continue

        class_slots = getattr(class_def, "slots", []) or []
        induced_slots = processor.schema_view.class_induced_slots(class_name)

        if slot_name in class_slots or slot_name in induced_slots:
            is_direct = slot_name in class_slots
            class_info = {
                "own": is_direct,
                "inherited": not is_direct,
                "required": False,  # Default value
            }

            # Check slot usage in the class
            if hasattr(class_def, "slot_usage"):
                slot_usage = getattr(class_def, "slot_usage", {}).get(slot_name)
                if slot_usage:
                    class_info.update(
                        {
                            "required": getattr(slot_usage, "required", False),
                            "multivalued": getattr(slot_usage, "multivalued", None),
                            "range": getattr(slot_usage, "range", None),
                        }
                    )

            usage[class_name] = class_info

    return usage


def prepare_slot_usage_stats(processor) -> Dict[str, Dict]:
    """Prepare usage statistics for slots."""
    stats = {}
    for slot_name in processor.schema_view.all_slots():
        usage = prepare_slot_usage_info(processor, slot_name)
        if usage:
            stats[slot_name] = {
                "usage": usage,
                "usage_count": len(usage),
                "required_count": sum(1 for info in usage.values() if info.get("required", False)),
            }
    return stats


def prepare_enum_usage_stats(processor) -> Dict[str, Dict]:
    """Prepare usage statistics for enums."""
    stats = {}
    for enum_name in processor.schema_view.all_enums():
        used_in_slots = []
        for slot_name, slot_def in processor.schema_view.all_slots().items():
            if getattr(slot_def, "range", None) == enum_name:
                used_in_slots.append(slot_name)

        stats[enum_name] = {
            "usage_count": len(used_in_slots),
            "used_in_slots": used_in_slots,
        }
    return stats


def prepare_hierarchy_data(processor) -> Dict[str, List[Dict]]:
    """
    Prepare class hierarchy data.
    """
    hierarchy = {}
    for class_name, class_def in processor.schema_view.all_classes().items():
        parent = getattr(class_def, "is_a", None)

        if parent not in hierarchy:
            hierarchy[parent] = []

        hierarchy[parent].append(
            {
                "name": class_name,
                "is_abstract": getattr(class_def, "abstract", False),
                "is_mixin": getattr(class_def, "mixin", False),
                "description": getattr(class_def, "description", ""),
            }
        )

    return hierarchy


def prepare_dependency_data(processor) -> Dict[str, List[Dict]]:
    """
    Prepare dependency relationships between schema elements.
    """
    dependencies = []

    # Add slot dependencies
    for slot_name, slot_def in processor.schema_view.all_slots().items():
        range_type = getattr(slot_def, "range", None)
        if range_type:
            if range_type in processor.schema_view.all_classes():
                dependencies.append(
                    {
                        "from": slot_name,
                        "to": range_type,
                        "type": "range",
                    }
                )

    # Add class inheritance dependencies
    for class_name, class_def in processor.schema_view.all_classes().items():
        parent = getattr(class_def, "is_a", None)
        if parent:
            dependencies.append(
                {
                    "from": class_name,
                    "to": parent,
                    "type": "inheritance",
                }
            )

        # Add mixin dependencies
        mixins = getattr(class_def, "mixins", [])
        for mixin in mixins:
            dependencies.append(
                {
                    "from": class_name,
                    "to": mixin,
                    "type": "mixin",
                }
            )

    return dependencies
