"""Download module."""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from tb_rest_client.rest import ApiException
from tb_rest_client.rest_client_ce import RestClientCE

from .utils import process_downloaded_data

logger = logging.getLogger(__name__)


def download_data_for_device(
    client: RestClientCE,
    device_name: str,
    start_time: datetime,
    end_time: datetime,
    variables: list[str] | None = None,
    interval: int | None = None,
    limit: int | None = None,
    agg: str | None = None,
) -> pd.DataFrame:
    """Download data for one device and create a Pandas dataframe.

    Args:
        client: The Thingsboard REST client.
        device_name: The name of the device to download data for.
        start_time: The start time for the data download.
        end_time: The end time for the data download.
        variables: The list of variables to download. If None, all
            variables will be downloaded.
        interval: Timeseries interval in milliseconds.
        limit: Maximum number of data points to fetch.
        agg: Aggregation type to use.

    Returns:
        A Pandas dataframe containing the downloaded data.
    """
    device_id = client.get_tenant_device(device_name).id

    # If no variables are provided, get all variables for the device
    if not variables:
        variables = client.get_timeseries_keys_v1(device_id)

    logger.info(
        f"Downloading data for {', '.join(variables)} for device {device_name}."
    )

    data = client.get_timeseries(
        entity_id=device_id,
        keys=",".join(variables),
        start_ts=int(start_time.timestamp() * 1000),
        end_ts=int(end_time.timestamp() * 1000),
        interval=interval,
        limit=limit,
        agg=agg,
    )

    df = process_downloaded_data(data, variables)
    return df


def get_data(
    thingsboard_url: str,
    credentials: dict,
    device_names: list[str],
    start_time: datetime,
    end_time: datetime,
    variables: list[str] | None = None,
    interval: int | None = None,
    limit: int | None = None,
    agg: str | None = None,
) -> list[pd.DataFrame]:
    """Downloads all data for a set of devices and variables.

    Args:
        thingsboard_url: The URL of the Thingsboard instance.
        credentials: A dictionary containing the authentication details.
        device_names: A list of device names to download data for.
        start_time: The start time for the data download.
        end_time: The end time for the data download.
        variables: A list of variables to download. If None, all variables
            will be downloaded.
        interval: Timeseries interval in milliseconds.
        limit: Maximum number of data points to fetch.
        agg: Aggregation type to use.

    Returns:
        A list of Pandas dataframes containing the downloaded data for each device.
    """
    dfs = []
    with RestClientCE(base_url=thingsboard_url) as client:
        try:
            if credentials["type"] == "api_key":
                client.api_key_login(credentials["value"])

            elif credentials["type"] == "password":
                client.login(credentials["username"], credentials["password"])

            else:
                logger.error("Invalid credentials provided.")
                raise ValueError(
                    "Invalid credentials type. Must be 'api_key' or 'password'."
                )
        except ApiException:
            logger.exception("Failed to authenticate with ThingsBoard")
            raise

        for device_name in device_names:
            df = download_data_for_device(
                client,
                device_name,
                start_time,
                end_time,
                variables,
                interval,
                limit,
                agg,
            )
            dfs.append(df)

    return dfs


def download_and_save(
    thingsboard_url: str,
    credentials: dict,
    device_names: list[str],
    start_time: datetime,
    end_time: datetime,
    output_dir: str | Path,
    variables: list[str] | None = None,
    interval: int | None = None,
    limit: int | None = None,
    agg: str | None = None,
) -> None:
    """Download data for a set of devices and save each to a CSV file.

    Args:
        thingsboard_url: The URL of the Thingsboard instance.
        credentials: A dictionary containing the authentication details.
        device_names: A list of device names to download data for.
        start_time: The start time for the data download.
        end_time: The end time for the data download.
        output_dir: Directory in which to save the output CSV files.
        variables: A list of variables to download. If None, all variables
            will be downloaded.
        interval: Timeseries interval in milliseconds.
        limit: Maximum number of data points to fetch.
        agg: Aggregation type to use.
    """
    output_dir = Path(output_dir)

    if output_dir.exists() and any(output_dir.iterdir()):
        response = input(
            f"'{output_dir}' already exists and is not empty. Continue? [y/N]"
        )
        if response.strip().lower() != "y":
            print("Abort.")
            return

    output_dir.mkdir(parents=True, exist_ok=True)

    dfs = get_data(
        thingsboard_url,
        credentials,
        device_names,
        start_time,
        end_time,
        variables,
        interval,
        limit,
        agg,
    )

    logger.info(f"Saving data to directory '{output_dir}'.")

    for device_name, df in zip(device_names, dfs):
        path = output_dir / f"{device_name}.csv"
        df.to_csv(path, index=True)
