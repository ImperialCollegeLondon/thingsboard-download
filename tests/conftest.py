"""Shared pytest fixtures."""

from unittest.mock import MagicMock

import pytest

SAMPLE_TOML = """\
[thingsboard]
url = "https://example.com"

[auth]
username = "user"
password = "pass"
api_key = "test_api_key"
public_id = "test_public_id"

[download]
devices = ["DEV001", "DEV002"]
variables = ["h", "t"]
start_time = "2026-08-01 09:00:00"
end_time = "2026-08-01 16:00:00"
output_dir = "."
"""


@pytest.fixture
def config_file(tmp_path):
    """Provides a fixture for the config file."""
    path = tmp_path / "config.toml"
    path.write_text(SAMPLE_TOML)
    return path


@pytest.fixture
def mock_client():
    """Provides a fixture for the client."""
    return MagicMock()
