# File: src/linkml_toolkit/visualization/core.py
"""Core visualization generation functionality with search capabilities."""

from pathlib import Path
from typing import Dict, Optional, List, Union
from datetime import datetime
import json
import logging
from dataclasses import dataclass
from linkml_runtime.utils.schemaview import SchemaView

from .utils import prepare_visualization_data
from .components import (
    generate_element_badges,
    generate_element_details,
    generate_class_details,
    generate_slot_details,
    generate_enum_details,
    generate_type_details,
)
import html

logger = logging.getLogger(__name__)


@dataclass
class VisualizationConfig:
    """Configuration for schema visualization."""

    show_descriptions: bool = True
    show_inheritance: bool = True
    show_usage_stats: bool = True
    show_validation: bool = True
    max_items_per_page: int = 50


class SchemaVisualizer:
    """Handles generation of schema visualizations and documentation."""

    def __init__(
        self,
        processor,
        viz_data: Optional[Dict] = None,
        config: Optional[VisualizationConfig] = None,
    ):
        """Initialize visualizer with a schema processor and optional pre-prepared data."""
        self.processor = processor
        self.schema_view = processor.schema_view
        self.viz_data = viz_data or prepare_visualization_data(processor)
        self.config = config or VisualizationConfig()

        # Handle undefined references gracefully by tracking them
        self.undefined_refs = []
        for slot_name, slot_def in self.schema_view.all_slots().items():
            domain = getattr(slot_def, "domain", None)
            if domain and domain not in self.schema_view.all_classes():
                self.undefined_refs.append({"type": "domain", "slot": slot_name, "value": domain})

    def generate_visualization(self, output_path: Optional[Union[str, Path]] = None) -> str:
        """Generate the main interactive HTML visualization."""
        content = self._generate_page_content()
        html_content = self._create_base_template(
            title=f"{self.viz_data['metadata'].get('name', 'Schema')} Visualization",
            content=content,
        )

        if output_path:
            self._save_html(html_content, output_path)

        return html_content

    def _generate_page_content(self) -> str:
        """Generate the main page content."""
        return f"""
            {self._generate_header()}
            <div class="flex pt-16">
                {self._generate_sidebar()}
                {self._generate_main_content()}
            </div>
        """

    def _create_base_template(self, title: str, content: str) -> str:
        """Create the base HTML template."""
        return f"""<!DOCTYPE html>
    <html lang="en" class="scroll-smooth">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.2.4/mermaid.min.js"></script>
        <style>
            .sidebar {{ height: calc(100vh - 4rem); }}
            .main-content {{ height: calc(100vh - 4rem); }}
            .search-highlight {{ background-color: rgba(145, 174, 183, 0.5); color: #000000; }}
            
            @media print {{
                .no-print {{ display: none; }}
                .page-break {{ page-break-before: always; }}
            }}
            
            .transition-transform {{
                transition: transform 0.3s ease-in-out;
            }}
            
            .rotate-180 {{
                transform: rotate(180deg);
            }}
        </style>
    </head>
    <body class="bg-gray-100">
        {content}
        <script>
            // Initialize mermaid for diagrams
            mermaid.initialize({{ startOnLoad: true }});

            // Toggle Functions for Schema Sections
            function toggleSection(sectionType) {{
                const list = document.getElementById(`${{sectionType}}-list`);
                const icon = document.getElementById(`${{sectionType}}-icon`);
                
                if (list && icon) {{
                    // Toggle the list visibility
                    if (list.classList.contains('hidden')) {{
                        list.classList.remove('hidden');
                        icon.classList.add('rotate-180');
                    }} else {{
                        list.classList.add('hidden');
                        icon.classList.remove('rotate-180');
                    }}
                }}
            }}

            // Toggle Details for Elements
            function toggleDetails(detailsId) {{
                const detailsElement = document.getElementById(detailsId);
                if (!detailsElement) return;

                // Find the parent card and then the button within it
                const parentCard = detailsElement.closest('[data-searchable="true"]');
                if (!parentCard) return;
                
                const button = parentCard.querySelector('button');
                if (!button) return;

                const buttonText = button.querySelector('.details-text');
                const buttonIcon = button.querySelector('svg');
                
                if (detailsElement.classList.contains('hidden')) {{
                    // Show details
                    detailsElement.classList.remove('hidden');
                    buttonText.textContent = 'Show less';
                    buttonIcon.classList.add('rotate-180');
                }} else {{
                    // Hide details
                    detailsElement.classList.add('hidden');
                    buttonText.textContent = 'Show more';
                    buttonIcon.classList.remove('rotate-180');
                }}
            }}

            // Initialize sidebar sections to be closed by default
            document.addEventListener('DOMContentLoaded', function() {{
                // Update the counts but keep sections closed
                const sections = document.querySelectorAll('[data-section-type]');
                sections.forEach(section => {{
                    const sectionType = section.dataset.sectionType;
                    const countElement = document.getElementById(`${{sectionType}}-count`);
                    const list = document.getElementById(`${{sectionType}}-list`);
                    
                    if (list && countElement) {{
                        const items = list.querySelectorAll('[data-searchable="true"]');
                        countElement.textContent = items.length;
                    }}
                }});
            }});

            // Search Functionality
            function filterElements() {{
                const query = document.getElementById('search-box').value.toLowerCase();
                const elements = document.querySelectorAll('[data-searchable="true"]');
                const sections = document.querySelectorAll('[data-section-type]');
                
                const totalCounts = {{}};
                elements.forEach(el => {{
                    const type = el.dataset.type;
                    if (!totalCounts[type]) {{
                        totalCounts[type] = 0;
                    }}
                    totalCounts[type]++;
                }});

                let visibleCount = {{}};

                elements.forEach(el => {{
                    el.style.display = '';
                    el.classList.remove('search-highlight');
                }});

                if (query) {{
                    elements.forEach(el => {{
                        const text = el.textContent.toLowerCase();
                        const type = el.dataset.type;

                        if (!visibleCount[type]) {{
                            visibleCount[type] = 0;
                        }}

                        if (text.includes(query)) {{
                            el.style.display = '';
                            el.classList.add('search-highlight');
                            visibleCount[type]++;
                            
                            // Show parent section when item matches
                            const parentSection = el.closest('[data-section-type]');
                            if (parentSection) {{
                                const sectionType = parentSection.dataset.sectionType;
                                const list = document.getElementById(`${{sectionType}}-list`);
                                const icon = document.getElementById(`${{sectionType}}-icon`);
                                if (list) {{
                                    list.classList.remove('hidden');
                                }}
                                if (icon) {{
                                    icon.classList.add('rotate-180');
                                }}
                            }}
                        }} else {{
                            el.style.display = 'none';
                        }}
                    }});

                    // Update counts for filtered results
                    Object.keys(totalCounts).forEach(type => {{
                        const countElement = document.getElementById(`${{type}}-count`);
                        if (countElement) {{
                            countElement.textContent = visibleCount[type] || 0;
                        }}
                    }});
                }} else {{
                    // Reset search state
                    sections.forEach(section => {{
                        const sectionType = section.dataset.sectionType;
                        const list = document.getElementById(`${{sectionType}}-list`);
                        const icon = document.getElementById(`${{sectionType}}-icon`);
                        const countElement = document.getElementById(`${{sectionType}}-count`);
                        
                        if (list) {{
                            list.classList.add('hidden');
                            // Get actual count of items in this section
                            const items = list.querySelectorAll('[data-searchable="true"]');
                            if (countElement) {{
                                countElement.textContent = items.length;
                            }}
                        }}
                        
                        if (icon) {{
                            icon.classList.remove('rotate-180');
                        }}
                    }});
                }}
            }}
        </script>
    </body>
    </html>"""

    def _generate_header(self) -> str:
        """Generate the header section."""
        metadata = self.viz_data["metadata"]

        return f"""
        <header class="bg-white shadow-md fixed w-full z-50 h-16">
            <div class="max-w-full mx-auto px-4 sm:px-6 lg:px-8 h-full">
                <div class="flex justify-between items-center h-full">
                    <div class="flex items-center">
                        <h1 class="text-xl font-bold text-gray-900">
                            {metadata.get('name', 'Schema')} Visualization
                        </h1>
                        <span class="ml-2 px-2 py-1 bg-gray-100 rounded text-sm">
                            {metadata.get('version', 'Unknown')}
                        </span>
                    </div>
                    <div class="flex items-center">
                        <input
                            type="text"
                            id="search-box"
                            class="border border-gray-300 rounded-lg px-4 py-2"
                            placeholder="Search..."
                            oninput="filterElements()"
                        />
                    </div>
                </div>
            </div>
        </header>
        """

    def _generate_sidebar(self) -> str:
        """Generate the navigation sidebar."""
        return f"""
        <aside class="w-64 bg-white shadow-md fixed h-full overflow-y-auto">
            <nav class="px-4 py-4">
                <div class="space-y-2">
                    <a href="#overview" class="block px-4 py-2 rounded hover:bg-gray-100 font-medium">Overview</a>
                    {self._generate_sidebar_sections()}
                </div>
            </nav>
        </aside>
        """

    def _save_html(self, content: str, output_path: Union[str, Path]) -> None:
        """Save HTML content to file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_stats_badges(self, stats: Dict[str, int]) -> str:
        """Generate the statistics badges."""
        badges = []
        colors = {"classes": "blue", "slots": "green", "enums": "yellow", "types": "purple"}

        for name, count in stats.items():
            color = colors.get(name, "gray")
            badges.append(
                f"""
                <div class="px-3 py-1 bg-{color}-50 rounded-lg">
                    <span class="text-sm font-medium">{name.title()}: {count}</span>
                </div>
            """
            )
        return "\n".join(badges)

    def _generate_sidebar_sections(self) -> str:
        """Generate sidebar navigation sections."""
        sections = []
        for section_name, items in self.viz_data["structure"].items():
            if items:
                sections.append(self._generate_sidebar_section(section_name, len(items)))
        return "\n".join(sections)

    def _generate_sidebar_section(self, name: str, count: int) -> str:
        """Generate a sidebar section."""
        section_type = name.lower()
        return f"""
        <div class="space-y-1" data-section-type="{section_type}">
            <button class="w-full flex items-center justify-between px-4 py-2 text-left rounded hover:bg-gray-100 font-medium"
                    onclick="toggleSection('{section_type}')">
                <span>{name.title()}</span>
                <div class="flex items-center">
                    <span id="{section_type}-count" data-type="{section_type}" class="text-sm text-gray-500 mr-2">{count}</span>
                    <svg class="h-5 w-5" id="{section_type}-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                    </svg>
                </div>
            </button>
            <div id="{section_type}-list" class="hidden pl-4 space-y-1">
                {self._generate_sidebar_links(self.viz_data['structure'][name], section_type)}
            </div>
        </div>
        """

    def _generate_sidebar_links(self, items: Dict, section_type: str) -> str:
        """Generate sidebar navigation links."""
        links = []
        for name in sorted(items.keys()):
            links.append(
                f"""
                <a href="#{section_type}-{name}" 
                class="block px-4 py-2 text-sm rounded hover:bg-gray-100 truncate" 
                data-searchable="true"
                data-type="{section_type}"
                title="{name}">
                    {name}
                </a>
            """
            )
        return "\n".join(links)

    def _generate_main_content(self) -> str:
        """Generate the main content area."""
        return f"""
        <main class="ml-64 flex-1 p-8 overflow-y-auto">
            {self._generate_overview_section()}
            {self._generate_element_sections()}
        </main>
        """

    def _generate_overview_section(self) -> str:
        """Generate the overview section."""
        metadata = self.viz_data["metadata"]
        structure = self.viz_data["structure"]

        counts = {
            "Classes": len(structure["classes"]),
            "Slots": len(structure["slots"]),
            "Enums": len(structure["enums"]),
            "Types": len(structure["types"]),
        }

        return f"""
        <section id="overview" class="mb-8">
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-2xl font-bold mb-4">Schema Overview</h2>
                <div class="grid grid-cols-2 gap-6">
                    <div>
                        <h3 class="text-lg font-semibold mb-2">Metadata</h3>
                        <dl class="grid grid-cols-2 gap-4">
                            {self._generate_metadata_list(metadata)}
                        </dl>
                    </div>
                    <div>
                        <h3 class="text-lg font-semibold mb-2">Summary</h3>
                        <div class="grid grid-cols-2 gap-4">
                            {self._generate_counts_grid(counts)}
                        </div>
                    </div>
                </div>
            </div>
        </section>
        """

    def _generate_counts_grid(self, counts: Dict[str, int]) -> str:
        """Generate the counts grid."""
        grid_items = []
        colors = {"Classes": "blue", "Slots": "green", "Enums": "yellow", "Types": "purple"}

        for name, count in counts.items():
            color = colors.get(name, "gray")
            grid_items.append(
                f"""
                <div class="p-4 bg-{color}-50 rounded-lg">
                    <div class="text-3xl font-bold text-{color}-600">{count}</div>
                    <div class="text-sm text-{color}-600">{name}</div>
                </div>
                """
            )
        return "\n".join(grid_items)

    def _generate_element_sections(self) -> str:
        """Generate sections for schema elements."""
        sections = []
        for section_name, items in self.viz_data["structure"].items():
            if items:
                sections.append(
                    self._generate_section(
                        title=section_name.title(), items=items, section_type=section_name
                    )
                )
        return "\n".join(sections)

    def _generate_section(self, title: str, items: Dict, section_type: str) -> str:
        """Generate a content section."""
        item_cards = []
        for name, info in sorted(items.items()):
            item_cards.append(self._generate_element_card(name, info, section_type))

        return f"""
        <section id="{section_type}" class="mb-8">
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-2xl font-bold mb-4">{title}</h2>
                <div class="grid gap-6">
                    {''.join(item_cards)}
                </div>
            </div>
        </section>
        """

    def _generate_element_card(self, name: str, info: Dict, element_type: str) -> str:
        """Generate a card for a schema element."""
        # Generate badges
        badges = []

        # Add type badge
        type_colors = {"class": "blue", "slot": "green", "enum": "yellow", "type": "purple"}
        badges.append(
            f'<span class="px-2 py-1 text-xs font-medium rounded-full bg-{type_colors.get(element_type, "gray")}-100 text-{type_colors.get(element_type, "gray")}-800">{element_type.title()}</span>'
        )

        # Add element-specific badges
        if element_type == "class":
            if info.get("abstract"):
                badges.append(
                    '<span class="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">Abstract</span>'
                )
            if info.get("slots"):
                badges.append(
                    f'<span class="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">{len(info["slots"])} slots</span>'
                )
        elif element_type == "slot":
            if info.get("required"):
                badges.append(
                    '<span class="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">Required</span>'
                )
            if info.get("range"):
                badges.append(
                    f'<span class="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">Range: {info["range"]}</span>'
                )
        elif element_type == "enum":
            if info.get("permissible_values"):
                badges.append(
                    f'<span class="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">{len(info["permissible_values"])} values</span>'
                )
            if info.get("used_in_slots"):
                badges.append(
                    f'<span class="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">{len(info["used_in_slots"])} slots</span>'
                )
        badges_html = "\n".join(badges)

        # Generate details content
        print(f"Generating details for {element_type} {name}")
        if element_type == "slots":
            details_content = generate_slot_details(info, self.schema_view)
        elif element_type == "enums":
            details_content = generate_enum_details(info, self.schema_view)
        else:
            details_content = generate_element_details(element_type, info, self.schema_view)

        # Generate unique ID for the element
        details_id = f"{element_type}-{name}-details"
        button_id = f"{element_type}-{name}-button"

        return f"""
        <div id="{element_type}-{name}" data-searchable="true" data-type="{element_type}" class="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow">
            <div class="p-4">
                <h3 class="text-lg font-semibold mb-2">{name}</h3>
                
                <div class="flex flex-wrap gap-2 mb-3">
                    {badges_html}
                </div>
                
                <div class="text-sm text-gray-600 mb-3">
                    {info.get('description', '')}
                </div>

                <div id="{details_id}" class="hidden border-t pt-3 mt-3">
                    {details_content}
                </div>
            </div>

            <button 
                id="{button_id}"
                onclick="toggleDetails('{details_id}')"
                class="w-full p-2 text-sm text-gray-500 hover:bg-gray-50 border-t flex items-center justify-center gap-1">
                <span class="details-text">Show more</span>
                <svg class="h-4 w-4 transform transition-transform duration-200" 
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
        """

    def _generate_hierarchy_section(self) -> str:
        """Generate an interactive schema explorer with an overview, graphs, and details."""

        # Prepare hierarchy data for classes and their slots
        def prepare_class_slot_hierarchy(schema_view):
            """
            Prepare data with classes and linked slots for visualization.

            Args:
                schema_view: A SchemaView object from linkml_runtime.

            Returns:
                dict: A hierarchical structure for classes, their slots, and related elements.
            """

            def build_tree(node_name, children_map, slot_map):
                """Recursively build a tree structure for classes and slots."""
                if node_name not in children_map:
                    return {
                        "name": node_name,
                        "type": "class",
                        "children": slot_map.get(node_name, []),
                    }
                return {
                    "name": node_name,
                    "type": "class",
                    "children": [
                        build_tree(child, children_map, slot_map)
                        for child in children_map[node_name]
                    ]
                    + slot_map.get(node_name, []),
                }

            # Map classes to their children (inheritance)
            children_map = {}
            for cls_name, cls_def in schema_view.all_classes().items():
                if cls_def.is_a:
                    parent = cls_def.is_a
                    children_map.setdefault(parent, []).append(cls_name)

            # Map classes to their slots
            slot_map = {}
            for slot_name, slot_def in schema_view.all_slots().items():
                domain = slot_def.domain
                if domain:
                    slot_info = {
                        "name": slot_name,
                        "type": "slot",
                        "range": slot_def.range or "Any",
                        "required": slot_def.required,
                    }
                    slot_map.setdefault(domain, []).append(slot_info)

            # Build the tree starting from root classes
            roots = [cls for cls in schema_view.all_classes() if cls not in children_map]
            return {
                "name": "Schema Classes",
                "children": [build_tree(root, children_map, slot_map) for root in roots],
            }

        # Prepare additional flat data for enums and types
        def prepare_flat_data(schema_view, element_type):
            """Prepare flat data for enums and types."""
            if element_type == "enums":
                return [
                    {
                        "name": enum_name,
                        "type": "enum",
                        "values": list(enum_def.permissible_values.keys()),
                    }
                    for enum_name, enum_def in schema_view.all_enums().items()
                ]
            elif element_type == "types":
                return [
                    {"name": type_name, "type": "type", "base": type_def.base}
                    for type_name, type_def in schema_view.all_types().items()
                ]
            return []

        # Generate the hierarchical and flat data
        classes_hierarchy = json.dumps(prepare_class_slot_hierarchy(self.schema_view))
        enums_data = json.dumps(prepare_flat_data(self.schema_view, "enums"))
        types_data = json.dumps(prepare_flat_data(self.schema_view, "types"))

        # Return the HTML, CSS, and JavaScript for the visualization
        return f"""
        <section id="schema-explorer" class="mb-8">
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-2xl font-bold mb-4">Schema Explorer</h2>

                <!-- Overview Section -->
                <div id="overview-dashboard" class="mb-6">
                    <div class="grid grid-cols-2 gap-6">
                        <canvas id="summary-chart" class="h-48"></canvas>
                        <div id="summary-metadata" class="text-gray-700">
                            <p><strong>Total Classes:</strong> {len(self.schema_view.all_classes())}</p>
                            <p><strong>Total Slots:</strong> {len(self.schema_view.all_slots())}</p>
                            <p><strong>Total Enums:</strong> {len(self.schema_view.all_enums())}</p>
                            <p><strong>Total Types:</strong> {len(self.schema_view.all_types())}</p>
                        </div>
                    </div>
                </div>

                <!-- Tabs for Navigation -->
                <div class="tabs mb-4">
                    <button class="tab-button active" onclick="showTab('classes')">Classes</button>
                    <button class="tab-button" onclick="showTab('enums')">Enums</button>
                    <button class="tab-button" onclick="showTab('types')">Types</button>
                </div>

                <!-- Tab Content -->
                <div id="classes" class="tab-content active">
                    <div id="classes-container" class="h-[600px]"></div>
                </div>
                <div id="enums" class="tab-content">
                    <div id="enums-container" class="h-[600px]"></div>
                </div>
                <div id="types" class="tab-content">
                    <div id="types-container" class="h-[600px]"></div>
                </div>

                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <script src="https://d3js.org/d3.v7.min.js"></script>
                <script>
                    const classData = {classes_hierarchy};
                    const enumData = {enums_data};
                    const typeData = {types_data};

                    // Initialize the summary chart
                    const ctx = document.getElementById('summary-chart').getContext('2d');
                    new Chart(ctx, {{
                        type: 'doughnut',
                        data: {{
                            labels: ['Classes', 'Slots', 'Enums', 'Types'],
                            datasets: [{{
                                data: [
                                    {len(self.schema_view.all_classes())},
                                    {len(self.schema_view.all_slots())},
                                    {len(self.schema_view.all_enums())},
                                    {len(self.schema_view.all_types())}
                                ],
                                backgroundColor: ['#4caf50', '#2196f3', '#ff9800', '#9c27b0'],
                            }}],
                        }},
                        options: {{
                            responsive: true,
                            plugins: {{
                                legend: {{
                                    position: 'bottom',
                                }},
                            }},
                        }},
                    }});

                    // Show the appropriate tab
                    function showTab(tabName) {{
                        document.querySelectorAll('.tab-content').forEach(tab => {{
                            tab.style.display = tab.id === tabName ? 'block' : 'none';
                        }});
                        document.querySelectorAll('.tab-button').forEach(button => {{
                            button.classList.toggle('active', button.textContent.toLowerCase() === tabName);
                        }});
                    }}

                    // Render the class hierarchy
                    const svg = d3.select("#classes-container").append("svg")
                        .attr("width", 1000)
                        .attr("height", 600);
                    const root = d3.hierarchy(classData);
                    const tree = d3.tree().size([600, 900])(root);

                    // Render tree links
                    svg.selectAll(".link")
                        .data(tree.links())
                        .join("path")
                        .attr("class", "link")
                        .attr("d", d3.linkHorizontal()
                            .x(d => d.y)
                            .y(d => d.x))
                        .attr("stroke", "#ccc")
                        .attr("fill", "none");

                    // Render tree nodes
                    svg.selectAll(".node")
                        .data(tree.descendants())
                        .join("g")
                        .attr("class", "node")
                        .attr("transform", d => `translate(${{d.y}}, ${{d.x}})`)
                        .each(function(d) {{
                            d3.select(this)
                                .append("circle")
                                .attr("r", 5)
                                .attr("fill", "#4caf50");

                            d3.select(this)
                                .append("text")
                                .attr("dx", 10)
                                .attr("dy", 3)
                                .text(d => d.data.name || 'Unnamed');
                        }});
                </script>

                <style>
                    .tab-button {{
                        padding: 10px 20px;
                        cursor: pointer;
                        border: none;
                        background: #f0f0f0;
                        transition: all 0.3s;
                    }}
                    .tab-button.active {{
                        background: #4caf50;
                        color: white;
                    }}
                    .tab-content {{
                        display: none;
                    }}
                    .tab-content.active {{
                        display: block;
                    }}
                    .node circle {{
                        fill: #4caf50;
                        cursor: pointer;
                    }}
                    .link {{
                        stroke: #ccc;
                        fill: none;
                    }}
                </style>
            </div>
        </section>
        """

    def _generate_hierarchy_diagram(self) -> str:
        """
        Deprecated method. Now uses React visualization.
        Kept for backwards compatibility.
        """
        return ""  # No longer needed

    def _generate_statistics_section(self) -> str:
        """Generate the usage statistics section."""
        return f"""
        <section id="statistics" class="mb-8">
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-2xl font-bold mb-4">Usage Statistics</h2>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                        <h3 class="text-lg font-semibold mb-3">Slot Usage</h3>
                        <div class="space-y-2">
                            {self._generate_slot_usage_list()}
                        </div>
                    </div>
                    <div>
                        <h3 class="text-lg font-semibold mb-3">Enum Usage</h3>
                        <div class="space-y-2">
                            {self._generate_enum_usage_list()}
                        </div>
                    </div>
                </div>
            </div>
        </section>
        """

    def _generate_slot_usage_list(self) -> str:
        """Generate list of slot usage stats."""
        slot_usage = self.viz_data.get("statistics", {}).get("slot_usage", {})
        if not slot_usage:
            return '<div class="text-gray-500">No slot usage information available</div>'

        items = []
        for slot_name, usage in sorted(
            slot_usage.items(), key=lambda x: len(x[1].get("usage", {})), reverse=True
        ):
            used_in = len(usage.get("usage", {}))
            items.append(
                f"""
                <div class="bg-gray-50 p-3 rounded">
                    <div class="flex justify-between items-center">
                        <span class="font-medium">{slot_name}</span>
                        <span class="text-sm text-gray-600">Used in {used_in} classes</span>
                    </div>
                </div>
            """
            )
        return "\n".join(items)

    def _generate_enum_usage_list(self) -> str:
        """Generate list of enum usage stats."""
        enum_usage = self.viz_data.get("statistics", {}).get("enum_usage", {})
        if not enum_usage:
            return '<div class="text-gray-500">No enum usage information available</div>'

        items = []
        for enum_name, usage in sorted(
            enum_usage.items(), key=lambda x: x[1].get("usage_count", 0), reverse=True
        ):
            usage_count = usage.get("usage_count", 0)
            items.append(
                f"""
                <div class="bg-gray-50 p-3 rounded">
                    <div class="flex justify-between items-center">
                        <span class="font-medium">{enum_name}</span>
                        <span class="text-sm text-gray-600">Used {usage_count} times</span>
                    </div>
                </div>
            """
            )
        return "\n".join(items)

    def _generate_metadata_list(self, metadata: Dict) -> str:
        """Generate metadata definition list."""
        items = []
        for key in ["name", "version", "description", "license"]:
            value = metadata.get(key, "Not specified")
            items.append(
                f"""
                <div class="col-span-2">
                    <dt class="text-sm font-medium text-gray-500">{key.title()}</dt>
                    <dd class="mt-1 text-sm text-gray-900">{value}</dd>
                </div>
                """
            )
        return "\n".join(items)

    def _generate_stats_grid(self) -> str:
        """Generate the statistics grid."""
        stats = self.viz_data["statistics"]["counts"]
        grid_items = []
        for name, count in stats.items():
            color = {"classes": "blue", "slots": "green", "enums": "yellow", "types": "purple"}.get(
                name, "gray"
            )

            grid_items.append(
                f"""
                <div class="p-4 bg-{color}-50 rounded-lg">
                    <div class="text-3xl font-bold text-{color}-600">{count}</div>
                    <div class="text-sm text-{color}-600">{name.title()}</div>
                </div>
            """
            )
        return f"""
            <div class="grid grid-cols-2 gap-4">
                {''.join(grid_items)}
            </div>
        """

    def generate_documentation(self, output_path: Path) -> None:
        """Generate full documentation bundle."""
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate main visualization
        index_path = output_path / "visualization.html"
        self.generate_visualization(index_path)

        # Generate hierarchy diagram
        hierarchy_path = output_path / "hierarchy.html"
        self._save_hierarchy_diagram(hierarchy_path)

        # Generate documentation pages for each element type
        self._generate_element_docs(output_path)
