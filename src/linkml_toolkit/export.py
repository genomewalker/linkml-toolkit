# File: src/linkml_toolkit/export.py
"""Export LinkML schemas to various formats."""

from pathlib import Path
from typing import Union, Dict, Optional, List
import logging
import json
import csv
from linkml_runtime.utils.schemaview import SchemaView
from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml.generators.rdfgen import RDFGenerator
from linkml.generators.graphqlgen import GraphqlGenerator
from .sql import SQLExporter, SQLDialect

logger = logging.getLogger(__name__)

class SchemaExporter:
    """Export LinkML schemas to various formats."""
    
    def __init__(self, schema_path: Union[str, Path]):
        """Initialize the schema exporter."""
        self.schema_path = Path(schema_path)
        self.schema_view = SchemaView(str(schema_path))
    
    def to_rdf(self, output_path: Union[str, Path], format: str = 'turtle') -> None:
        """Export schema to RDF."""
        output_path = Path(output_path)
        
        try:
            # Use RDFLib for RDF generation
            from rdflib import Graph, Namespace, URIRef, Literal
            from rdflib.namespace import RDF, RDFS, OWL
            
            # Create a new graph
            graph = Graph()
            
            # Get the schema
            schema = self.schema_view.schema
            
            # Create a namespace for the schema
            namespace = Namespace(f"http://example.org/{schema.name}#")
            graph.namespace_manager.bind(schema.name, namespace)
            
            # Add basic schema metadata
            schema_node = URIRef(namespace[schema.name])
            graph.add((schema_node, RDF.type, OWL.Ontology))
            
            # Add classes
            for class_name, class_def in self.schema_view.all_classes().items():
                class_node = URIRef(namespace[class_name])
                graph.add((class_node, RDF.type, OWL.Class))
                
                # Add class description if available
                if class_def.description:
                    graph.add((class_node, RDFS.comment, Literal(class_def.description)))
            
            # Add slots
            for slot_name, slot_def in self.schema_view.all_slots().items():
                slot_node = URIRef(namespace[slot_name])
                graph.add((slot_node, RDF.type, RDF.Property))
                
                # Add slot description if available
                if slot_def.description:
                    graph.add((slot_node, RDFS.comment, Literal(slot_def.description)))
            
            # Serialize the graph
            output_path.parent.mkdir(parents=True, exist_ok=True)
            graph.serialize(destination=str(output_path), format=format)
        
        except Exception as e:
            logger.error(f"Error exporting RDF: {e}")
            raise ValueError(f"Failed to export RDF: {e}")
    
    def to_json_schema(self, output_path: Union[str, Path]) -> None:
        """Export schema to JSON Schema."""
        output_path = Path(output_path)
        generator = JsonSchemaGenerator(self.schema_view.schema)
        json_schema = generator.serialize()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_schema)
    
    def to_graphql(self, output_path: Union[str, Path]) -> None:
        """Export schema to GraphQL."""
        output_path = Path(output_path)
        generator = GraphqlGenerator(self.schema_view.schema)
        graphql_schema = generator.serialize()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(graphql_schema)

    def to_sql(self, output_path: Union[str, Path], dialect: str = 'postgresql') -> None:
        """Export schema to SQL DDL statements.
        
        Args:
            output_path: Path to save the SQL file
            dialect: SQL dialect to use ('postgresql', 'mysql', 'sqlite', or 'duckdb')
        """
        output_path = Path(output_path)
        dialect_enum = SQLDialect(dialect)
        exporter = SQLExporter(self.schema_view)
        exporter.save_sql(output_path, dialect_enum)



    def to_csv(self, output_dir: Union[str, Path], delimiter: str = ',') -> None:
        """Export schema components to CSV/TSV files.
        
        Args:
            output_dir: Directory where CSV files will be created
            delimiter: Field delimiter (',' for CSV, '\t' for TSV)
        """
        output_dir = Path(output_dir)
        
        # Ensure output_dir is a directory
        if output_dir.exists() and not output_dir.is_dir():
            raise ValueError(f"Output path {output_dir} must be a directory.")
        
        output_dir.mkdir(parents=True, exist_ok=True)

        def ensure_valid_file_path(file_path: Path) -> Path:
            """Ensure the given file_path is a valid file."""
            if file_path.is_dir():
                raise ValueError(f"Expected a file path, but got a directory: {file_path}")
            return file_path

        # Export classes
        classes_file = ensure_valid_file_path(output_dir / f'classes{".tsv" if delimiter == "\\t" else ".csv"}')
        self._write_csv(
            classes_file,
            ['name', 'description', 'slots', 'is_a', 'mixins', 'abstract', 'tree_root'],
            [
                {
                    'name': class_name,
                    'description': class_def.description or '',
                    'slots': ', '.join(class_def.slots or []),
                    'is_a': class_def.is_a or '',
                    'mixins': ', '.join(class_def.mixins or []),
                    'abstract': str(class_def.abstract or False),
                    'tree_root': str(class_def.tree_root or False)
                }
                for class_name, class_def in self.schema_view.all_classes().items()
            ],
            delimiter
        )

        # Export slots
        slots_file = ensure_valid_file_path(output_dir / f'slots{".tsv" if delimiter == "\\t" else ".csv"}')
        self._write_csv(
            slots_file,
            ['name', 'description', 'range', 'required', 'multivalued', 'pattern', 
            'identifier', 'key', 'minimum_value', 'maximum_value'],
            [
                {
                    'name': slot_name,
                    'description': slot_def.description or '',
                    'range': slot_def.range or '',
                    'required': str(slot_def.required or False),
                    'multivalued': str(slot_def.multivalued or False),
                    'pattern': slot_def.pattern or '',
                    'identifier': str(slot_def.identifier or False),
                    'key': str(slot_def.key or False),
                    'minimum_value': str(slot_def.minimum_value) if slot_def.minimum_value is not None else '',
                    'maximum_value': str(slot_def.maximum_value) if slot_def.maximum_value is not None else ''
                }
                for slot_name, slot_def in self.schema_view.all_slots().items()
            ],
            delimiter
        )

        # Export enums
        enums_file = ensure_valid_file_path(output_dir / f'enums{".tsv" if delimiter == "\\t" else ".csv"}')
        enums_data = []
        for enum_name, enum_def in self.schema_view.all_enums().items():
            permissible_values = enum_def.permissible_values or {}
            for value_name, value_def in permissible_values.items():
                enums_data.append({
                    'enum_name': enum_name,
                    'enum_description': enum_def.description or '',
                    'value': value_name,
                    'value_description': value_def.description or '',
                    'value_meaning': value_def.meaning or ''
                })

        self._write_csv(
            enums_file,
            ['enum_name', 'enum_description', 'value', 'value_description', 'value_meaning'],
            enums_data,
            delimiter
        )

        # Export types
        types_file = ensure_valid_file_path(output_dir / f'types{".tsv" if delimiter == "\\t" else ".csv"}')
        self._write_csv(
            types_file,
            ['name', 'description', 'base', 'uri', 'pattern'],
            [
                {
                    'name': type_name,
                    'description': type_def.description or '',
                    'base': type_def.typeof or '',
                    'uri': type_def.uri or '',
                    'pattern': type_def.pattern or ''
                }
                for type_name, type_def in self.schema_view.all_types().items()
            ],
            delimiter
        )

    def _write_csv(self, file_path: Path, fieldnames: List[str], data: List[Dict], delimiter: str = ',') -> None:
        """Helper method to write CSV/TSV files."""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)