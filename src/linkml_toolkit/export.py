"""Export LinkML schemas to various formats."""

from pathlib import Path
from typing import Union, Dict, Optional
import logging
from linkml_runtime.utils.schemaview import SchemaView
from linkml_runtime.dumpers import json_schema_dumper, rdf_dumper, graphql_dumper
import rdflib

logger = logging.getLogger(__name__)


class SchemaExporter:
    """Export LinkML schemas to various formats."""

    def __init__(self, schema_path: Union[str, Path]):
        """Initialize the schema exporter."""
        self.schema_path = Path(schema_path)
        self.schema_view = SchemaView(str(schema_path))

    def to_json_schema(self, output_path: Union[str, Path]) -> None:
        """Export schema to JSON Schema."""
        output_path = Path(output_path)
        json_schema = json_schema_dumper.JSONSchemaDumper().dump(
            self.schema_view.schema
        )

        with open(output_path, "w") as f:
            f.write(json_schema)

    def to_rdf(self, output_path: Union[str, Path], format: str = "turtle") -> None:
        """Export schema to RDF."""
        output_path = Path(output_path)
        graph = rdf_dumper.RDFDumper().dump(self.schema_view.schema)

        if isinstance(graph, rdflib.Graph):
            graph.serialize(destination=str(output_path), format=format)
        else:
            raise ValueError("Failed to generate RDF graph")

    def to_graphql(self, output_path: Union[str, Path]) -> None:
        """Export schema to GraphQL."""
        output_path = Path(output_path)
        graphql_schema = graphql_dumper.GraphQLDumper().dump(self.schema_view.schema)

        with open(output_path, "w") as f:
            f.write(graphql_schema)
