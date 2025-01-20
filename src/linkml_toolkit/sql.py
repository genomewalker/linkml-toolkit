# File: src/linkml_toolkit/sql.py
"""SQL export functionality for LinkML schemas."""

from enum import Enum
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path


class SQLDialect(Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    DUCKDB = "duckdb"


@dataclass
class SQLTypeMap:
    """Mapping of LinkML types to SQL types for different dialects."""

    sqlite: str
    postgresql: str
    mysql: str
    duckdb: str


# Default type mappings for different SQL dialects
TYPE_MAPPINGS = {
    "string": SQLTypeMap(sqlite="TEXT", postgresql="TEXT", mysql="TEXT", duckdb="VARCHAR"),
    "integer": SQLTypeMap(sqlite="INTEGER", postgresql="INTEGER", mysql="INT", duckdb="INTEGER"),
    "boolean": SQLTypeMap(
        sqlite="INTEGER",  # SQLite doesn't have native boolean
        postgresql="BOOLEAN",
        mysql="BOOLEAN",
        duckdb="BOOLEAN",
    ),
    "float": SQLTypeMap(
        sqlite="REAL", postgresql="DOUBLE PRECISION", mysql="DOUBLE", duckdb="DOUBLE"
    ),
    "decimal": SQLTypeMap(sqlite="REAL", postgresql="DECIMAL", mysql="DECIMAL", duckdb="DECIMAL"),
    "datetime": SQLTypeMap(
        sqlite="TEXT", postgresql="TIMESTAMP", mysql="DATETIME", duckdb="TIMESTAMP"
    ),
    "date": SQLTypeMap(sqlite="TEXT", postgresql="DATE", mysql="DATE", duckdb="DATE"),
    "time": SQLTypeMap(sqlite="TEXT", postgresql="TIME", mysql="TIME", duckdb="TIME"),
    "uri": SQLTypeMap(sqlite="TEXT", postgresql="TEXT", mysql="TEXT", duckdb="VARCHAR"),
}


class SQLExporter:
    """Export LinkML schema to SQL DDL statements."""

    def __init__(self, schema_view):
        """Initialize the SQL exporter."""
        self.schema_view = schema_view
        self._fkey_statements = []

    def get_sql_type(self, range_type: str, dialect: SQLDialect) -> str:
        """Get the SQL type for a LinkML type in the specified dialect."""
        type_map = TYPE_MAPPINGS.get(range_type)
        if type_map is None:
            # Default to text type if no mapping exists
            type_map = TYPE_MAPPINGS["string"]
        return getattr(type_map, dialect.value)

    def generate_sql(self, dialect: SQLDialect = SQLDialect.POSTGRESQL) -> str:
        """Generate SQL DDL statements for the schema."""
        statements = []
        self._fkey_statements = []  # Reset foreign key statements

        # Add header comment
        statements.append(f"-- Generated SQL schema for {self.schema_view.schema.name}")
        statements.append("-- SQL Dialect: " + dialect.value)
        statements.append("")

        # Generate ENUM types for PostgreSQL
        if dialect == SQLDialect.POSTGRESQL:
            for enum_name, enum_def in self.schema_view.all_enums().items():
                enum_values = enum_def.permissible_values or {}
                if enum_values:
                    values_str = ", ".join(f"'{v}'" for v in enum_values.keys())
                    statements.append(f"CREATE TYPE {enum_name}_enum AS ENUM ({values_str});")

        # Generate tables for each class
        for class_name, class_def in self.schema_view.all_classes().items():
            table_statements = []
            table_statements.append(f"CREATE TABLE {class_name} (")

            # Get all slots for the class
            slots = []
            for slot_name in class_def.slots or []:
                slot_def = self.schema_view.get_slot(slot_name)
                if slot_def:
                    slots.append((slot_name, slot_def))

            # Generate column definitions
            column_defs = []
            primary_key = None

            for slot_name, slot_def in slots:
                # Determine column type
                range_type = slot_def.range
                if range_type in self.schema_view.all_enums() and dialect == SQLDialect.POSTGRESQL:
                    sql_type = f"{range_type}_enum"
                else:
                    sql_type = self.get_sql_type(range_type, dialect)

                # Build column definition
                col_def = f"    {slot_name} {sql_type}"

                # Add constraints
                constraints = []
                if slot_def.required:
                    constraints.append("NOT NULL")
                if slot_def.identifier:
                    primary_key = slot_name
                if slot_def.pattern:
                    if dialect in [SQLDialect.POSTGRESQL, SQLDialect.MYSQL]:
                        constraints.append(f"CHECK ({slot_name} ~ '{slot_def.pattern}')")
                if slot_def.minimum_value is not None:
                    constraints.append(f"CHECK ({slot_name} >= {slot_def.minimum_value})")
                if slot_def.maximum_value is not None:
                    constraints.append(f"CHECK ({slot_name} <= {slot_def.maximum_value})")

                if constraints:
                    col_def += " " + " ".join(constraints)

                column_defs.append(col_def)

                # Handle foreign key references
                if range_type in self.schema_view.all_classes():
                    fk_name = f"fk_{class_name}_{slot_name}"
                    fk_stmt = (
                        f"ALTER TABLE {class_name} "
                        f"ADD CONSTRAINT {fk_name} "
                        f"FOREIGN KEY ({slot_name}) "
                        f"REFERENCES {range_type} ({primary_key});"
                    )
                    self._fkey_statements.append(fk_stmt)

            # Add primary key if it exists
            if primary_key:
                column_defs.append(f"    PRIMARY KEY ({primary_key})")

            # Combine all column definitions
            table_statements.append(",\n".join(column_defs))
            table_statements.append(");")
            statements.extend(table_statements)
            statements.append("")

        # Add foreign key constraints after all tables are created
        if self._fkey_statements:
            statements.append("-- Foreign Key Constraints")
            statements.extend(self._fkey_statements)

        return "\n".join(statements)

    def save_sql(
        self, output_path: Union[str, Path], dialect: SQLDialect = SQLDialect.POSTGRESQL
    ) -> None:
        """Save SQL DDL statements to a file."""
        sql = self.generate_sql(dialect)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(sql)
