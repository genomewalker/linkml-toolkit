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

    # Core properties section with better styling
    core_props = []
    if info.get("description"):
        core_props.append(("Description", info["description"]))
    if info.get("title"):
        core_props.append(("Title", info["title"]))
    if info.get("slot_uri"):
        core_props.append(
            (
                "URI",
                f'<code class="px-2 py-1 bg-gray-100 rounded text-sm">{info["slot_uri"]}</code>',
            )
        )

    # Status flags with nicer badges
    status_list = []
    if info.get("required", False):
        status_list.append(
            '<span class="px-2 py-1 text-xs font-medium rounded bg-red-100 text-red-800 border border-red-200">Required</span>'
        )
    if info.get("recommended", False):
        status_list.append(
            '<span class="px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-800 border border-blue-200">Recommended</span>'
        )
    if info.get("multivalued", False):
        status_list.append(
            '<span class="px-2 py-1 text-xs font-medium rounded bg-purple-100 text-purple-800 border border-purple-200">Multivalued</span>'
        )

    if status_list:
        core_props.append(("Status", " ".join(status_list)))

    # Range information with special handling for enums
    if info.get("range"):
        range_value = info["range"]
        if schema_view and schema_view.get_enum(range_value):
            enum_def = schema_view.get_enum(range_value)
            enum_values = getattr(enum_def, "permissible_values", {})
            if enum_values:
                enum_id = f"enum_{range_value}".replace(" ", "_")

                # Create accordion items for enum values
                enum_items = []
                for k, v in enum_values.items():
                    description = getattr(v, "description", "") or ""
                    enum_items.append(
                        f"""
                        <div class="p-3 bg-blue-50 rounded-lg mb-2 hover:bg-blue-100 transition-colors">
                            <div class="font-medium text-blue-700">{k}</div>
                            {f'<div class="text-sm text-blue-600 mt-1">{description}</div>' if description else ''}
                        </div>
                    """
                    )

                range_html = f"""
                    <div>
                        <div class="mb-2">
                            <div class="flex items-center">
                                <code class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm font-medium">Enum: {range_value}</code>
                                <button 
                                    onclick="toggleEnumValues('{enum_id}')"
                                    class="ml-2 text-blue-600 hover:text-blue-800 text-sm flex items-center">
                                    <span class="enum-toggle-text">Show values</span>
                                    <svg class="h-4 w-4 ml-1 transform transition-transform duration-200 enum-toggle-icon" 
                                         fill="none" 
                                         stroke="currentColor" 
                                         viewBox="0 0 24 24">
                                        <path stroke-linecap="round" 
                                              stroke-linejoin="round" 
                                              stroke-width="2" 
                                              d="M19 9l-7 7-7-7"/>
                                    </svg>
                                </button>
                            </div>
                        </div>
                        <div id="{enum_id}" class="hidden mt-2">
                            {''.join(enum_items)}
                        </div>
                    </div>
                """
                core_props.append(("Range", range_html))
        else:
            core_props.append(
                (
                    "Range",
                    f'<code class="px-2 py-1 bg-gray-100 rounded text-sm">{range_value}</code>',
                )
            )

    if core_props:
        sections.append(
            f"""
            <div class="mb-6 bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                <div class="px-4 py-3 border-b border-gray-200 bg-gray-50">
                    <h4 class="text-sm font-medium text-gray-900">Core Properties</h4>
                </div>
                <div class="p-4">
                    <dl class="grid grid-cols-1 gap-4">
                        {"".join(f'''
                            <div class="sm:grid sm:grid-cols-3 sm:gap-4">
                                <dt class="text-sm font-medium text-gray-500">{k}</dt>
                                <dd class="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{v}</dd>
                            </div>''' for k, v in core_props)}
                    </dl>
                </div>
            </div>
            """
        )

        # Add toggle function for enums to the script section
        sections.append(
            """
            <script>
                function toggleEnumValues(enumId) {
                    const container = document.getElementById(enumId);
                    const button = event.currentTarget;
                    const text = button.querySelector('.enum-toggle-text');
                    const icon = button.querySelector('.enum-toggle-icon');
                    
                    if (container.classList.contains('hidden')) {
                        container.classList.remove('hidden');
                        text.textContent = 'Hide values';
                        icon.classList.add('rotate-180');
                    } else {
                        container.classList.add('hidden');
                        text.textContent = 'Show values';
                        icon.classList.remove('rotate-180');
                    }
                }
            </script>
        """
        )

    # Validation Rules section with improved card styling
    validation_props = []
    if info.get("pattern"):
        validation_props.append(
            (
                "Pattern",
                f'<code class="text-sm bg-gray-100 px-2 py-1 rounded">{html.escape(info["pattern"])}</code>',
            )
        )
    if info.get("string_serialization"):
        validation_props.append(
            (
                "String Format",
                f'<code class="text-sm bg-gray-100 px-2 py-1 rounded">{html.escape(info["string_serialization"])}</code>',
            )
        )
    if info.get("structured_pattern"):
        pattern = info["structured_pattern"]
        if isinstance(pattern, dict):
            syntax = pattern.get("syntax", "")
            if syntax:
                validation_props.append(
                    (
                        "Structured Pattern",
                        f'<code class="text-sm bg-gray-100 px-2 py-1 rounded">{html.escape(syntax)}</code>',
                    )
                )

    if validation_props:
        sections.append(
            f"""
            <div class="mb-6 bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                <div class="px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-white">
                    <h4 class="text-sm font-medium text-purple-900">Validation Rules</h4>
                </div>
                <div class="p-4">
                    <dl class="grid grid-cols-1 gap-4">
                        {"".join(f'''
                            <div class="p-3 bg-purple-50 rounded-lg">
                                <dt class="text-sm font-medium text-purple-800 mb-1">{k}</dt>
                                <dd class="text-sm text-purple-900 pl-2 border-l-2 border-purple-200">{v}</dd>
                            </div>
                        ''' for k, v in validation_props)}
                    </dl>
                </div>
            </div>
            """
        )

    # Examples section
    if info.get("examples"):
        example_items = []
        for ex in info["examples"]:
            if isinstance(ex, dict):
                value = ex.get("value", "")
                description = ex.get("description", "")
            else:
                value = getattr(ex, "value", str(ex))
                description = getattr(ex, "description", "")

            example_items.append(
                f"""
                <div class="bg-green-50 p-3 rounded-lg hover:bg-green-100 transition-colors">
                    <code class="text-sm font-medium text-green-700">{html.escape(str(value))}</code>
                    {f'<div class="text-sm text-green-600 mt-1">{html.escape(description)}</div>' if description else ''}
                </div>
            """
            )

        if example_items:
            sections.append(
                f"""
                <div class="mb-6 bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                    <div class="px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-green-50 to-white">
                        <h4 class="text-sm font-medium text-green-900">Examples</h4>
                    </div>
                    <div class="p-4">
                        <div class="space-y-3">{"".join(example_items)}</div>
                    </div>
                </div>
                """
            )

    # Annotations section
    if info.get("annotations"):
        annotation_items = []
        for key, value in info["annotations"].items():
            if hasattr(value, "tag") and hasattr(value, "value"):
                annotation_value = value.value
                extensions = getattr(value, "extensions", {})
                if extensions:
                    annotation_value = f"{annotation_value}\nExtensions: {extensions}"
            else:
                annotation_value = str(value)

            annotation_items.append(
                f"""
                <div class="bg-amber-50 p-3 rounded-lg hover:bg-amber-100 transition-colors">
                    <div class="font-medium text-sm text-amber-800 mb-1">{html.escape(key)}</div>
                    <div class="pl-2 border-l-2 border-amber-200">
                        <code class="text-sm text-amber-700">{html.escape(str(annotation_value))}</code>
                    </div>
                </div>
            """
            )

        if annotation_items:
            sections.append(
                f"""
                <div class="mb-6 bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                    <div class="px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-amber-50 to-white">
                        <h4 class="text-sm font-medium text-amber-900">Annotations</h4>
                    </div>
                    <div class="p-4">
                        <div class="space-y-3">{"".join(annotation_items)}</div>
                    </div>
                </div>
                """
            )

    return (
        "\n".join(sections)
        if sections
        else '<p class="text-sm text-gray-500">No additional details available</p>'
    )


def generate_enum_details(info: Dict, schema_view) -> str:
    """Generate detailed content for an enum."""
    sections = []

    # Core properties section
    core_props = []
    if info.get("description"):
        core_props.append(("Description", info["description"]))
    if info.get("title"):
        core_props.append(("Title", info["title"]))

    if core_props:
        sections.append(
            f"""
            <div class="mb-4">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Core Properties</h4>
                <dl class="grid grid-cols-1 gap-2">
                    {"".join(f'<div><dt class="text-sm font-medium text-gray-600">{k}</dt><dd class="text-sm text-gray-800 ml-4">{v}</dd></div>' for k, v in core_props)}
                </dl>
            </div>
            """
        )

    # Permissible Values section
    if info.get("permissible_values"):
        value_items = []
        for value_name, value_info in sorted(info["permissible_values"].items()):
            description = value_info.get("description", "")
            meaning = value_info.get("meaning", "")
            value_items.append(
                f"""
                <div class="bg-gray-50 p-3 rounded mb-2">
                    <div class="font-medium text-gray-800">{html.escape(value_name)}</div>
                    {f'<div class="text-sm text-gray-600 mt-1">{html.escape(description)}</div>' if description else ''}
                    {f'<div class="text-sm text-gray-500 mt-1">Meaning: {html.escape(meaning)}</div>' if meaning else ''}
                </div>
                """
            )

        if value_items:
            sections.append(
                f"""
                <div class="mb-4">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Permissible Values</h4>
                    <div class="space-y-2">{"".join(value_items)}</div>
                </div>
                """
            )

    # Find all slots that reference this enum
    used_in_slots = []
    if schema_view:
        enum_name = info.get("name")
        for slot_name, slot_def in schema_view.all_slots().items():
            if getattr(slot_def, "range", None) == enum_name:
                slot_info = {
                    "name": slot_name,
                    "description": getattr(slot_def, "description", ""),
                    "required": getattr(slot_def, "required", False),
                    "recommended": getattr(slot_def, "recommended", False),
                }
                used_in_slots.append(slot_info)

    if used_in_slots:
        sections.append(
            f"""
            <div class="mb-4">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Used in Slots</h4>
                <div class="space-y-2">
                    {generate_slot_usage_section(used_in_slots)}
                </div>
            </div>
            """
        )

    return (
        "\n".join(sections)
        if sections
        else '<p class="text-sm text-gray-500">No additional details available</p>'
    )


def generate_slot_usage_section(slots: List[Dict]) -> str:
    """Generate HTML for displaying slot usage information."""
    items = []
    for slot in sorted(slots, key=lambda x: x["name"]):
        # Generate status badges
        badges = []
        if slot.get("required"):
            badges.append(
                '<span class="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">Required</span>'
            )
        if slot.get("recommended"):
            badges.append(
                '<span class="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">Recommended</span>'
            )

        badges_html = f'<div class="flex gap-2 mt-1">{"".join(badges)}</div>' if badges else ""

        items.append(
            f"""
            <div class="bg-gray-50 p-3 rounded">
                <div class="font-medium text-gray-800">{html.escape(slot["name"])}</div>
                {f'<div class="text-sm text-gray-600 mt-1">{html.escape(slot["description"])}</div>' if slot.get("description") else ''}
                {badges_html}
            </div>
            """
        )
    return "\n".join(items)


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
