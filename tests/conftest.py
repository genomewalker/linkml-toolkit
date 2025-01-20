import pytest
from pathlib import Path


@pytest.fixture
def test_data_dir():
    return Path(__file__).parent / "data"


@pytest.fixture
def basic_schema(test_data_dir):
    return test_data_dir / "basic_schema.yaml"


@pytest.fixture
def second_schema(test_data_dir):
    return test_data_dir / "second_schema.yaml"


@pytest.fixture
def invalid_schema(test_data_dir):
    return test_data_dir / "invalid_schema.yaml"
