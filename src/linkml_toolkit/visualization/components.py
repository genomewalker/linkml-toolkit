# File: src/linkml_toolkit/visualization/components.py
"""Individual visualization components."""

from typing import Dict, List, Any, Optional
import html


def generate_badge(text: str, color: str, size: str = "sm") -> str:
    """Generate a badge with specified text and color."""
    return f"""
        <span class="px-2 py-0.5 text-{size} font-medium rounded-full 
                     bg-{color}-100 text-{color}-800">
            {html.escape(text)}
        </span>
    """


def generate_element_badges(element_type: str, info: Dict) -> str:
    """Generate badges for a schema element."""
    badges = []

    # Common badges
    if info.get("deprecated", False):
        badges.append(generate_badge("Deprecated", "red"))

    # Type-specific badges
    if element_type == "class":
        if info.get("abstract", False):
            badges.append(generate_badge("Abstract", "gray"))
        if info.get("mixin", False):
            badges.append(generate_badge("Mixin", "blue"))
        if info.get("tree_root", False):
            badges.append(generate_badge("Root", "green"))
        if info.get("slots"):
            badges.append(generate_badge(f'{len(info["slots"])} slots', "purple"))

    elif element_type == "slot":
        if info.get("required", False):
            badges.append(generate_badge("Required", "red"))
        if info.get("multivalued", False):
            badges.append(generate_badge("Multivalued", "blue"))
        if info.get("key", False):
            badges.append(generate_badge("Key", "purple"))
        if info.get("range"):
            badges.append(generate_badge(f'Range: {info["range"]}', "green"))

    elif element_type == "enums":
        value_count = len(info.get("permissible_values", {}))
        if value_count > 0:
            badges.append(generate_badge(f"{value_count} values", "yellow"))

    elif element_type == "type":
        if info.get("typeof"):
            badges.append(generate_badge(f'Base: {info["typeof"]}', "blue"))

    return " ".join(badges)


def generate_element_details(element_type: str, info: Dict, schema_view) -> str:
    """Generate detailed content for a schema element."""
    sections = []

    # Common metadata section for all elements
    metadata_items = []
    for key in ["title", "description", "comments", "in_subset", "slot_uri", "class_uri"]:
        if info.get(key):
            if isinstance(info[key], list):
                metadata_items.append((key.title(), ", ".join(info[key])))
            else:
                metadata_items.append((key.title(), info[key]))

    if metadata_items:
        sections.append(
            f"""
            <div class="mb-4">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Metadata</h4>
                <dl class="grid grid-cols-1 gap-2">
                    {"".join(f'<div><dt class="text-sm font-medium text-gray-600">{k}</dt><dd class="text-sm text-gray-800 ml-4">{v}</dd></div>' for k, v in metadata_items)}
                </dl>
            </div>
            """
        )

    # Type-specific sections
    if element_type == "slot":
        # Core Properties
        properties = []
        for prop in [
            "range",
            "required",
            "recommended",
            "multivalued",
            "pattern",
            "string_serialization",
        ]:
            if info.get(prop) is not None:
                if isinstance(info[prop], bool):
                    properties.append((prop.title(), "Yes" if info[prop] else "No"))
                else:
                    properties.append((prop.title(), info[prop]))

        if properties:
            sections.append(
                f"""
                <div class="mb-4">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Properties</h4>
                    <dl class="grid grid-cols-1 gap-2">
                        {"".join(f'<div><dt class="text-sm font-medium text-gray-600">{k}</dt><dd class="text-sm text-gray-800 ml-4">{v}</dd></div>' for k, v in properties)}
                    </dl>
                </div>
                """
            )

        # Examples
        if info.get("examples"):
            examples = [ex.get("value", str(ex)) for ex in info["examples"] if ex]
            if examples:
                sections.append(
                    f"""
                    <div class="mb-4">
                        <h4 class="text-sm font-medium text-gray-700 mb-2">Examples</h4>
                        <ul class="list-disc pl-5 text-sm text-gray-600">
                            {"".join(f'<li>{ex}</li>' for ex in examples)}
                        </ul>
                    </div>
                    """
                )

        # Annotations
        if info.get("annotations"):
            sections.append(
                f"""
                <div class="mb-4">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Annotations</h4>
                    <dl class="grid grid-cols-1 gap-2">
                        {"".join(f'<div><dt class="text-sm font-medium text-gray-600">{k}</dt><dd class="text-sm text-gray-800 ml-4">{v}</dd></div>' for k, v in info["annotations"].items())}
                    </dl>
                </div>
                """
            )

    elif element_type == "class":
        # Inheritance and Mixins
        if info.get("is_a") or info.get("mixins"):
            inheritance = []
            if info.get("is_a"):
                inheritance.append(("Inherits from", info["is_a"]))
            if info.get("mixins"):
                inheritance.append(("Mixins", ", ".join(info["mixins"])))

            sections.append(
                f"""
                <div class="mb-4">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Inheritance</h4>
                    <dl class="grid grid-cols-1 gap-2">
                        {"".join(f'<div><dt class="text-sm font-medium text-gray-600">{k}</dt><dd class="text-sm text-gray-800 ml-4">{v}</dd></div>' for k, v in inheritance)}
                    </dl>
                </div>
                """
            )

        # Slots Section
        if info.get("slots"):
            slot_items = []
            for slot_name, slot_info in info["slots"].items():
                slot_data = []
                # Basic slot info
                slot_data.append(f'<div class="font-medium text-gray-800">{slot_name}</div>')

                # Slot properties
                for prop in ["description", "range", "required", "multivalued"]:
                    if slot_info.get(prop) is not None:
                        if isinstance(slot_info[prop], bool):
                            slot_data.append(
                                f'{prop.title()}: {"Yes" if slot_info[prop] else "No"}'
                            )
                        else:
                            slot_data.append(f"{prop.title()}: {slot_info[prop]}")

                # Examples if any
                if slot_info.get("examples"):
                    examples = [ex.get("value", str(ex)) for ex in slot_info["examples"] if ex]
                    if examples:
                        slot_data.append(f'Examples: {", ".join(examples)}')

                slot_items.append(
                    f"""
                    <div class="bg-gray-50 p-3 rounded mb-2">
                        {"<br>".join(slot_data)}
                    </div>
                    """
                )

            sections.append(
                f"""
                <div class="mb-4">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Slots</h4>
                    <div class="space-y-2">{"".join(slot_items)}</div>
                </div>
                """
            )

    elif element_type == "enums":
        value_items = []
        for value_name, value_info in sorted(info.get("permissible_values", {}).items()):
            value_data = [f'<div class="font-medium text-gray-800">{html.escape(value_name)}</div>']

            if value_info:
                if value_info.get("description"):
                    value_data.append(
                        f'<div class="text-sm text-gray-600">{html.escape(value_info["description"])}</div>'
                    )
                if value_info.get("meaning"):
                    value_data.append(
                        f'<div class="text-sm text-gray-500">Meaning: {html.escape(value_info["meaning"])}</div>'
                    )

            value_items.append(
                f"""
                <div class="bg-gray-50 p-3 rounded mb-2">
                    {"<br>".join(value_data)}
                </div>
                """
            )

        # Permissible Values section
        if value_items:
            sections.append(
                f"""
                <div class="mb-4">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Permissible Values</h4>
                    <div class="space-y-2">{"".join(value_items)}</div>
                </div>
                """
            )

        # Used in Slots section
        if info.get("used_in_slots"):
            sections.append(
                f"""
                <div class="mb-4">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Used in Slots</h4>
                    <div class="flex flex-wrap gap-2">
                        {"".join(f'<span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">{html.escape(slot)}</span>' for slot in info["used_in_slots"])}
                    </div>
                </div>
                """
            )

    # Return full content or placeholder
    return (
        "\n".join(sections)
        if sections
        else '<p class="text-sm text-gray-500">No additional details available</p>'
    )


def generate_class_details(info: Dict, schema_view) -> str:
    """Generate detailed content for a class."""
    sections = []

    # Slots section with detailed properties
    if info.get("slots"):
        slot_items = []
        for slot_name in sorted(info["slots"]):
            slot = schema_view.get_slot(slot_name)
            if slot:
                # Collect all relevant properties
                properties = []
                if getattr(slot, "description", None):
                    properties.append(("Description", slot.description))
                if getattr(slot, "range", None):
                    properties.append(("Range", slot.range))
                if getattr(slot, "required", None) is not None:
                    properties.append(("Required", "Yes" if slot.required else "No"))
                if getattr(slot, "recommended", None) is not None:
                    properties.append(("Recommended", "Yes" if slot.recommended else "No"))
                if getattr(slot, "multivalued", None) is not None:
                    properties.append(("Multivalued", "Yes" if slot.multivalued else "No"))
                if getattr(slot, "pattern", None):
                    properties.append(("Pattern", slot.pattern))

                # Add examples if available
                examples = getattr(slot, "examples", [])
                if examples:
                    example_values = [ex.get("value", str(ex)) for ex in examples if ex]
                    if example_values:
                        properties.append(("Examples", ", ".join(example_values)))

                slot_items.append(
                    f"""
                    <div class="bg-gray-50 p-3 rounded mb-2">
                        <div class="font-medium text-gray-800 mb-2">{html.escape(slot_name)}</div>
                        <dl class="grid grid-cols-1 gap-1">
                            {"".join(f'<div class="mb-1"><dt class="text-sm font-medium text-gray-600">{k}</dt><dd class="text-sm text-gray-800 ml-4">{v}</dd></div>' for k, v in properties)}
                        </dl>
                    </div>
                    """
                )

        if slot_items:
            sections.append(
                f"""
                <div class="mb-4">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Slots</h4>
                    <div class="space-y-2">{"".join(slot_items)}</div>
                </div>
                """
            )

    # Class metadata section
    metadata_items = []
    if info.get("description"):
        metadata_items.append(("Description", info["description"]))
    if info.get("is_a"):
        metadata_items.append(("Inherits from", info["is_a"]))
    if info.get("abstract"):
        metadata_items.append(("Abstract", "Yes"))
    if info.get("mixin"):
        metadata_items.append(("Mixin", "Yes"))
    if info.get("class_uri"):
        metadata_items.append(("URI", info["class_uri"]))

    if metadata_items:
        sections.append(
            f"""
            <div class="mb-4">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Class Metadata</h4>
                <dl class="grid grid-cols-1 gap-2">
                    {"".join(f'<div><dt class="text-sm font-medium text-gray-600">{k}</dt><dd class="text-sm text-gray-800 ml-4">{v}</dd></div>' for k, v in metadata_items)}
                </dl>
            </div>
            """
        )

    return (
        "\n".join(sections)
        if sections
        else '<p class="text-sm text-gray-500">No additional details available</p>'
    )


def generate_slot_details(info: Dict, schema_view) -> str:
    """Generate detailed content for a slot."""
    sections = []

    # Core properties
    properties = []
    if info.get("description"):
        properties.append(("Description", info["description"]))
    if info.get("range"):
        properties.append(("Range", info["range"]))
    if info.get("required") is not None:
        properties.append(("Required", "Yes" if info["required"] else "No"))
    if info.get("recommended") is not None:
        properties.append(("Recommended", "Yes" if info["recommended"] else "No"))
    if info.get("multivalued") is not None:
        properties.append(("Multivalued", "Yes" if info["multivalued"] else "No"))
    if info.get("pattern"):
        properties.append(("Pattern", info["pattern"]))
    if info.get("slot_uri"):
        properties.append(("URI", info["slot_uri"]))

    # Examples
    if info.get("examples"):
        examples = [ex.get("value", str(ex)) for ex in info["examples"] if ex]
        if examples:
            properties.append(("Examples", ", ".join(examples)))

    # Annotations
    if info.get("annotations"):
        for key, value in info["annotations"].items():
            properties.append((f"Annotation: {key}", value))

    if properties:
        sections.append(
            f"""
            <div class="mb-4">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Properties</h4>
                <dl class="grid grid-cols-1 gap-2">
                    {"".join(f'<div><dt class="text-sm font-medium text-gray-600">{k}</dt><dd class="text-sm text-gray-800 ml-4">{v}</dd></div>' for k, v in properties)}
                </dl>
            </div>
            """
        )

    return (
        "\n".join(sections)
        if sections
        else '<p class="text-sm text-gray-500">No additional details available</p>'
    )


def generate_enum_details(info: Dict) -> str:
    """Generate detailed content for an enum."""
    sections = []
    # Enum values section
    if info.get("permissible_values"):
        value_items = []
        for value_name, value_info in sorted(info["permissible_values"].items()):
            value_items.append(
                f"""
                <div class="bg-gray-50 p-3 rounded mb-2">
                    <div class="font-medium text-gray-800">{html.escape(value_name)}</div>
                    {f'<div class="text-sm text-gray-600 mt-1">{html.escape(str(value_info.get("description", "")))}</div>' if value_info.get("description") else ''}
                </div>
                """
            )

        sections.append(
            f"""
            <div class="mb-4">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Permissible Values</h4>
                <div class="space-y-2">{"".join(value_items)}</div>
            </div>
            """
        )

    # Used in slots
    if info.get("used_in_slots"):
        sections.append(
            f"""
            <div class="mb-4">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Used in Slots</h4>
                <div class="flex flex-wrap gap-2">
                    {"".join(f'<span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">{html.escape(slot)}</span>' for slot in info["used_in_slots"])}
                </div>
            </div>
            """
        )

    return (
        "\n".join(sections)
        if sections
        else '<p class="text-sm text-gray-500">No additional details available</p>'
    )


def generate_type_details(info: Dict) -> str:
    """Generate detailed content for a type."""
    sections = []

    if info.get("typeof"):
        sections.append(
            f"""
            <div class="mb-4">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Base Type</h4>
                <div class="text-sm text-gray-600">{html.escape(info['typeof'])}</div>
            </div>
        """
        )

    if info.get("uri"):
        sections.append(
            f"""
            <div class="mb-4">
                <h4 class="text-sm font-medium text-gray-700 mb-2">URI</h4>
                <div class="text-sm text-gray-600">{html.escape(info['uri'])}</div>
            </div>
        """
        )

    return (
        "\n".join(sections)
        if sections
        else '<p class="text-sm text-gray-500">No additional details available</p>'
    )
