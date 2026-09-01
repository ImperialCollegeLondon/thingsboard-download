"""Tests for download.py."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from thingsboard_download.download import (
    download_and_save,
    download_data_for_device,
    get_data,
    get_device_id,
)

START = datetime(2026, 8, 1, 9, 0, 0)
END = datetime(2026, 8, 1, 16, 0, 0)
TIMESERIES_DATA = {"h": [{"ts": 1785595829313, "value": "1.5"}]}


def _setup_mock_ce(mock_ce):
    """Configure a mock RestClientCE context manager with timeseries data."""
    mock_client = MagicMock()
    mock_ce.return_value.__enter__.return_value = mock_client
    mock_client.get_tenant_device.return_value.id = MagicMock()
    mock_client.get_timeseries.return_value = TIMESERIES_DATA
    return mock_client


@patch("thingsboard_download.download.get_device_id")
def test_download_data_for_device(mock_get_device_id, mock_client):
    """Tests the download_data_for_device function."""
    mock_get_device_id.return_value = "device-123"
    mock_client.get_timeseries.return_value = TIMESERIES_DATA

    df = download_data_for_device(mock_client, "DEV001", START, END, ["h"])

    mock_get_device_id.assert_called_once_with("DEV001", mock_client, None)
    assert "h" in df.columns


@patch("thingsboard_download.download.get_device_id")
def test_download_data_for_device_no_variables(mock_get_device_id, mock_client):
    """Tests that all variable keys are fetched when none are specified."""
    mock_get_device_id.return_value = "device-123"
    mock_client.get_timeseries_keys_v1.return_value = ["h"]
    mock_client.get_timeseries.return_value = TIMESERIES_DATA

    download_data_for_device(mock_client, "DEV001", START, END)

    mock_get_device_id.assert_called_once_with("DEV001", mock_client, None)
    mock_client.get_timeseries_keys_v1.assert_called_once()


def test_get_device_id_tenant(mock_client):
    """Tests that get_tenant_device is used when no public_id is given."""
    mock_client.get_tenant_device.return_value.id = "device-123"

    device_id = get_device_id("DEV001", mock_client)

    mock_client.get_tenant_device.assert_called_once_with("DEV001")
    mock_client.get_customer_devices.assert_not_called()
    assert device_id == "device-123"


def test_get_device_id_public_first_page(mock_client):
    """Tests that a matching device is returned from the first page of results."""
    device = MagicMock()
    device.id = "device-123"
    device.name = "DEV001"

    mock_client.get_customer_devices.return_value = MagicMock(
        data=[device], has_next=False
    )

    device_id = get_device_id("DEV001", mock_client, public_id="public-id")

    mock_client.get_customer_devices.assert_called_once_with("public-id", 1000, 0)
    mock_client.get_tenant_device.assert_not_called()
    assert device_id == "device-123"


def test_get_device_id_public_paginates(mock_client):
    """Tests that subsequent pages are fetched when no match is found."""
    device = MagicMock()
    device.id = "device-123"
    device.name = "DEV001"

    other_device = MagicMock()
    other_device.id = "other-id"
    other_device.name = "OTHER"

    mock_client.get_customer_devices.side_effect = [
        MagicMock(data=[other_device], has_next=True),
        MagicMock(data=[device], has_next=False),
    ]

    device_id = get_device_id("DEV001", mock_client, public_id="public-id")

    assert mock_client.get_customer_devices.call_args_list == [
        (("public-id", 1000, 0),),
        (("public-id", 1000, 1),),
    ]
    assert device_id == "device-123"


def test_get_device_id_public_not_found(mock_client):
    """Tests that None is returned when no page contains a matching device."""
    other_device = MagicMock()
    other_device.id = "other-id"
    other_device.name = "OTHER"

    mock_client.get_customer_devices.return_value = MagicMock(
        data=[other_device], has_next=False
    )

    device_id = get_device_id("DEV001", mock_client, public_id="public-id")

    mock_client.get_tenant_device.assert_not_called()
    assert device_id is None


@patch("thingsboard_download.download.RestClientCE")
def test_get_data_api_key(mock_ce):
    """Tests that api_key_login is called within get_data with api_key credentials."""
    mock_client = _setup_mock_ce(mock_ce)

    get_data(
        thingsboard_url="https://example.com",
        credentials={"type": "api_key", "value": "key"},
        device_names=["DEV001"],
        start_time=START,
        end_time=END,
        variables=["h"],
    )

    mock_client.api_key_login.assert_called_once_with("key")


@patch("thingsboard_download.download.RestClientCE")
def test_get_data_password(mock_ce):
    """Tests that login is called within get_data with password credentials."""
    mock_client = _setup_mock_ce(mock_ce)

    get_data(
        thingsboard_url="https://example.com",
        credentials={"type": "password", "username": "user", "password": "pass"},
        device_names=["DEV001"],
        start_time=START,
        end_time=END,
        variables=["h"],
    )

    mock_client.login.assert_called_once_with("user", "pass")


@patch("thingsboard_download.download.get_device_id")
@patch("thingsboard_download.download.RestClientCE")
def test_get_data_public_id(mock_ce, mock_get_device_id):
    """Tests that public_login is used and get_device_id receives the public_id."""
    mock_client = _setup_mock_ce(mock_ce)
    mock_get_device_id.return_value = "device-123"

    get_data(
        thingsboard_url="https://example.com",
        credentials={"type": "public_id", "value": "public-id"},
        device_names=["DEV001"],
        start_time=START,
        end_time=END,
        variables=["h"],
    )

    mock_client.public_login.assert_called_once_with("public-id")
    mock_get_device_id.assert_called_once_with("DEV001", mock_client, "public-id")


@patch("thingsboard_download.download.RestClientCE")
def test_get_data_invalid_credentials(mock_ce):
    """Tests that get_data raises a ValueError for an invalid credentials type."""
    _setup_mock_ce(mock_ce)

    with pytest.raises(ValueError, match="Invalid credentials type"):
        get_data(
            thingsboard_url="https://example.com",
            credentials={"type": "invalid"},
            device_names=["DEV001"],
            start_time=START,
            end_time=END,
            variables=["h"],
        )


@patch("thingsboard_download.download.RestClientCE")
def test_download_and_save(mock_ce, tmp_path):
    """Tests the download_and_save function creates an output CSV."""
    _setup_mock_ce(mock_ce)

    download_and_save(
        thingsboard_url="https://example.com",
        credentials={"type": "api_key", "value": "key"},
        device_names=["DEV001"],
        start_time=START,
        end_time=END,
        output_dir=tmp_path / "out",
        variables=["h"],
    )

    assert (tmp_path / "out" / "DEV001.csv").exists()


@patch("builtins.input", return_value="n")
@patch("thingsboard_download.download.RestClientCE")
def test_download_and_save_existing_dir_abort(mock_ce, mock_input, tmp_path):
    """Tests that the download is aborted when the user declines to overwrite."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "existing.csv").write_text("data")
    assert (out_dir / "existing.csv").exists()

    download_and_save(
        thingsboard_url="https://example.com",
        credentials={"type": "api_key", "value": "key"},
        device_names=["DEV001"],
        start_time=START,
        end_time=END,
        output_dir=out_dir,
        variables=["h"],
    )

    mock_ce.assert_not_called()
    assert not (out_dir / "DEV001.csv").exists()


@patch("builtins.input", return_value="y")
@patch("thingsboard_download.download.RestClientCE")
def test_download_and_save_existing_dir_continue(mock_ce, mock_input, tmp_path):
    """Tests that the download proceeds when the user confirms overwrite."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "existing.csv").write_text("data")
    assert (out_dir / "existing.csv").exists()
    _setup_mock_ce(mock_ce)

    download_and_save(
        thingsboard_url="https://example.com",
        credentials={"type": "api_key", "value": "key"},
        device_names=["DEV001"],
        start_time=START,
        end_time=END,
        output_dir=out_dir,
        variables=["h"],
    )

    mock_ce.assert_called()
    assert (out_dir / "DEV001.csv").exists()
