import pytest
from app import detect


@pytest.fixture(scope="session", autouse=True)
def _rules():
    detect.load_rules()
