"""Config module."""

import os
import tomllib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def load_config(
    source: str | Path = Path(__file__).parent.parent / "config.toml",
) -> dict[str, Any]:
    """Load configuration from file.

    Args:
        source: The path to the TOML configuration file. Defaults to "config.toml".

    Returns:
        A dictionary containing the configuration data.
    """
    with open(source, "rb") as f:
        config = tomllib.load(f)

    return config


def load_device_details(
    source: str | Path = Path(__file__).parent.parent / "config.toml",
) -> tuple[
    list[str], list[str] | None, datetime, datetime, int | None, int | None, str | None
]:
    """Load the details for the data download.

    Args:
        source: The path to the TOML configuration file. Defaults to "config.toml".

    Returns:
        A tuple containing the list of devices, list of variables, start time,
            end time, interval, limit and aggregation.
    """
    config = load_config(source)
    download = config.get("download", {})

    devices = (
        os.getenv("DEVICES").split(",")
        if os.getenv("DEVICES")
        else download.get("devices")
    )
    if not devices:
        raise ValueError(
            "No device name(s) provided. Provide device names using an environment "
            "variable or the config.toml file."
        )

    variables = (
        os.getenv("VARIABLES").split(",")
        if os.getenv("VARIABLES")
        else download.get("variables")
    )

    interval = os.getenv("INTERVAL", download.get("interval"))
    interval = int(interval) if interval is not None else None

    limit = os.getenv("LIMIT", download.get("limit"))
    limit = int(limit) if limit is not None else None

    agg = os.getenv("AGG", download.get("agg"))

    if start_time := os.getenv("START_TIME", download.get("start_time")):
        start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

    if end_time := os.getenv("END_TIME", download.get("end_time")):
        end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

    # If only one of start_time or end_time is provided, raise an error
    if (start_time is None) != (end_time is None):
        raise ValueError("Both start_time and end_time must be provided together.")

    # If neither start_time nor end_time is provided, default to the last 30 days
    if end_time is None:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)

    return devices, variables, start_time, end_time, interval, limit, agg


def load_credentials(
    source: str | Path = Path(__file__).parent.parent / "config.toml",
) -> dict[str, Any]:
    """Load configuration from environment variables and/or a TOML file.

    Args:
        source: The path to the TOML configuration file. Defaults to "config.toml".

    Returns:
        A dictionary containing the Thingsboard URL and authentication credentials.
    """
    config = load_config(source)

    # Get the Thingsboard URL
    tb_url = os.getenv("THINGSBOARD_URL", config.get("thingsboard", {}).get("url"))
    if not tb_url:
        raise ValueError(
            "No Thingsboard URL provided. Provide a URL using an environment variable"
            " or the config.toml file."
        )

    # Get authentication details from env vars or config file
    auth = config.get("auth", {})
    username = os.getenv("THINGSBOARD_USERNAME", auth.get("username"))
    password = os.getenv("THINGSBOARD_PASSWORD", auth.get("password"))
    api_key = os.getenv("THINGSBOARD_API_KEY", auth.get("api_key"))

    if api_key:
        credentials = {"type": "api_key", "value": api_key}
    elif username and password:
        credentials = {"type": "password", "username": username, "password": password}
    else:
        raise ValueError(
            "No authentication details provided. Provide either an API key or username"
            " and password using environment variables or the config.toml file."
        )

    return {"thingsboard_url": tb_url, "credentials": credentials}
