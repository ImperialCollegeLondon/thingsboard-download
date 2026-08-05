"""Tests for config.py."""

from datetime import datetime

import pytest

from thingsboard_download.config import (
    load_config,
    load_credentials,
    load_device_details,
)


def test_load_config(config_file):
    """Tests the load_config function."""
    config = load_config(config_file)
    assert config["thingsboard"]["url"] == "https://example.com"
    assert config["auth"]["username"] == "user"
    assert config["download"]["devices"] == ["DEV001", "DEV002"]


def test_load_device_details_from_config(config_file):
    """Tests the load_device_details function with a config file."""
    devices, variables, start_time, end_time, interval, limit, agg = (
        load_device_details(config_file)
    )
    assert devices == ["DEV001", "DEV002"]
    assert variables == ["h", "t"]
    assert start_time == datetime(2026, 8, 1, 9, 0, 0)
    assert end_time == datetime(2026, 8, 1, 16, 0, 0)
    assert interval is None
    assert limit is None
    assert agg is None


def test_load_device_details_from_env_var(config_file, monkeypatch):
    """Tests the load_device_details function with env vars."""
    monkeypatch.setenv("DEVICES", "DEV003,DEV004")
    monkeypatch.setenv("VARIABLES", "var1,var2")
    devices, variables, start_time, end_time, interval, limit, agg = (
        load_device_details(config_file)
    )
    assert devices == ["DEV003", "DEV004"]
    assert variables == ["var1", "var2"]
    assert start_time == datetime(2026, 8, 1, 9, 0, 0)
    assert end_time == datetime(2026, 8, 1, 16, 0, 0)
    assert interval is None
    assert limit is None
    assert agg is None


def test_load_device_details_optional_timeseries_from_env_var(config_file, monkeypatch):
    """Tests optional timeseries settings are loaded from env vars."""
    monkeypatch.setenv("INTERVAL", "60000")
    monkeypatch.setenv("LIMIT", "500")
    monkeypatch.setenv("AGG", "AVG")

    _, _, _, _, interval, limit, agg = load_device_details(config_file)

    assert interval == 60000
    assert limit == 500
    assert agg == "AVG"


def test_load_device_details_default_times(tmp_path):
    """Test load_device_details uses the last 30 days are used as default."""
    (tmp_path / "config.toml").write_text(
        """\
[thingsboard]
url = "https://example.com"

[auth]
api_key = "test_api_key"

[download]
devices = ["DEV001", "DEV002"]
variables = ["h", "t"]
output_dir = "."
"""
    )
    _, _, start_time, end_time, interval, limit, agg = load_device_details(
        tmp_path / "config.toml"
    )
    today = datetime.today()
    assert today.day == end_time.day
    assert today.month == end_time.month
    assert (end_time - start_time).days == 30
    assert start_time.hour == 0
    assert interval is None
    assert limit is None
    assert agg is None


def test_load_device_details_optional_timeseries_from_config(tmp_path):
    """Tests optional timeseries settings are loaded from config."""
    (tmp_path / "config.toml").write_text(
        """\
[thingsboard]
url = "https://example.com"

[auth]
api_key = "test_api_key"

[download]
devices = ["DEV001"]
start_time = "2026-08-01 09:00:00"
end_time = "2026-08-01 16:00:00"
interval = 120000
limit = 200
agg = "MAX"
"""
    )

    _, _, _, _, interval, limit, agg = load_device_details(tmp_path / "config.toml")

    assert interval == 120000
    assert limit == 200
    assert agg == "MAX"


def test_load_device_details_no_devices(tmp_path):
    """Test load_device_details raises an error with no devices."""
    (tmp_path / "config.toml").write_text(
        """\
    [thingsboard]
    url = "https://example.com"

    [auth]
    api_key = "test_api_key"

    [download]
    variables = ["h", "t"]
    output_dir = "."
    """
    )
    with pytest.raises(ValueError, match="No device name"):
        load_device_details(tmp_path / "config.toml")


def test_load_device_details_missing_time(tmp_path):
    """Test load_device_details raises an error when time missing."""
    (tmp_path / "config.toml").write_text(
        """\
[thingsboard]
url = "https://example.com"

[auth]
api_key = "test_api_key"

[download]
devices = ["DEV001"]
variables = ["h", "t"]
output_dir = "."
start_time = "2026-08-01 09:00:00"
"""
    )
    with pytest.raises(ValueError, match="Both start_time and end_time"):
        load_device_details(tmp_path / "config.toml")


def test_load_credentials(config_file):
    """Test the load_credentials function."""
    result = load_credentials(config_file)
    assert result["thingsboard_url"] == "https://example.com"
    assert result["credentials"]["type"] == "api_key"
    assert result["credentials"]["value"] == "test_api_key"


def test_load_credentials_password(tmp_path):
    """Test the load_credentials function with a password."""
    (tmp_path / "config.toml").write_text(
        """\
    [thingsboard]
    url = "https://example.com"

    [auth]
    username = "user"
    password = "password"
    """
    )
    result = load_credentials(tmp_path / "config.toml")
    assert result["credentials"]["type"] == "password"
    assert result["credentials"]["username"] == "user"


def test_load_credentials_no_url(tmp_path):
    """Test load_credentials raises an error with no URL."""
    (tmp_path / "config.toml").write_text(
        """\
        [auth]
        username = "user"
        password = "password"
        """
    )
    with pytest.raises(ValueError, match="No Thingsboard URL"):
        load_credentials(tmp_path / "config.toml")


def test_load_credentials_no_auth(tmp_path):
    """Test load_credentials raises an error with no auth details."""
    (tmp_path / "config.toml").write_text(
        """\
    [thingsboard]
    url = "https://example.com"
    """
    )
    with pytest.raises(ValueError, match="No authentication details"):
        load_credentials(tmp_path / "config.toml")
