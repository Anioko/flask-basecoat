import pytest

from .live_server import ensure_server, stop_server


@pytest.fixture(scope="session", autouse=True)
def _live_server():
    """Start the browser test server once per test session."""
    ensure_server()
    yield
    stop_server()
