import os
import pytest
from pathlib import Path
import tempfile


@pytest.fixture(scope="session")
def test_data_dir():
    """
    Create a temporary directory for test data that persists for the entire test session.
    """
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "test_data"
        data_dir.mkdir(parents=True, exist_ok=True)

        # Create basic schema
        basic_schema_path = data_dir / "basic_schema.yaml"
        basic_schema_path.write_text(
            """
name: basic_schema
id: https://example.org/basic_schema
description: A basic test schema with valid configuration

types:
  string:
    uri: https://w3id.org/linkml/String
    base: str
  integer:
    uri: https://w3id.org/linkml/Integer
    base: int

classes:
  Person:
    attributes:
      name:
        range: string
        required: true
      age:
        range: integer

slots:
  name:
    range: string
    required: true
  age:
    range: integer
"""
        )

        # Create second schema
        second_schema_path = data_dir / "second_schema.yaml"
        second_schema_path.write_text(
            """
name: second_schema
id: https://example.org/second_schema
description: A second test schema with additional information

types:
  string:
    uri: https://w3id.org/linkml/String
    base: str

classes:
  Address:
    attributes:
      street:
        range: string
      city:
        range: string

slots:
  street:
    range: string
  city:
    range: string
"""
        )

        # Create invalid schema
        invalid_schema_path = data_dir / "invalid_schema.yaml"
        invalid_schema_path.write_text(
            """
name: invalid_schema
description: A schema missing critical configuration

classes:
  InvalidEntity:
    description: An entity without proper schema configuration
"""
        )

        # Yield the data directory path
        yield data_dir


@pytest.fixture
def basic_schema(test_data_dir):
    """Fixture for a basic valid schema."""
    return test_data_dir / "basic_schema.yaml"


@pytest.fixture
def second_schema(test_data_dir):
    """Fixture for a second schema to test merging."""
    return test_data_dir / "second_schema.yaml"


@pytest.fixture
def invalid_schema(test_data_dir):
    """Fixture for an invalid schema to test validation."""
    return test_data_dir / "invalid_schema.yaml"
