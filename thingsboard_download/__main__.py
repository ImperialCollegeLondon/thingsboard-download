"""Main module."""

import os
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from .config import load_config, load_credentials, load_device_details
from .download import download_and_save

load_dotenv()


def main() -> None:
    """Run the data download using the user's configuration details.

    Configuration details can be provided by argparse, environment variables
    or the config file. The thingsboard URL and connection credentials must
    be provided using the environment variables or config file. A file is
    saved for each device to the output directory. If an output directory
    already exists, a warning is provided.
    """
    parser = ArgumentParser(description="Download data from Thingsboard.")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path(__file__).parent.parent / "config.toml",
        metavar="FILE",
        help="Path to the config TOML file (config.toml as default).",
    )
    parser.add_argument(
        "-d",
        "--devices",
        nargs="+",
        metavar="DEVICE",
        help="Device name(s) to download data for. Overrides config/env.",
    )
    parser.add_argument(
        "-v",
        "--variables",
        nargs="+",
        metavar="VAR",
        help="Variable name(s) to download data for. Overrides config/env.",
    )
    parser.add_argument(
        "-s",
        "--start-time",
        metavar="DATETIME",
        help="Start time in 'YYYY-MM-DD HH:MM:SS' format. Overrides config/env.",
    )
    parser.add_argument(
        "-e",
        "--end-time",
        metavar="DATETIME",
        help="End time in 'YYYY-MM-DD HH:MM:SS' format. Overrides config/env.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        metavar="DIR",
        help="Directory to save output CSV files. Overrides config/env.",
    )
    args = parser.parse_args()

    devices, variables, start_time, end_time = load_device_details(args.config)
    connection = load_credentials(args.config)

    if args.devices:
        devices = args.devices
    if args.variables:
        variables = args.variables
    if args.start_time:
        start_time = datetime.strptime(args.start_time, "%Y-%m-%d %H:%M:%S")
    if args.end_time:
        end_time = datetime.strptime(args.end_time, "%Y-%m-%d %H:%M:%S")

    if args.output_dir:
        output_dir = args.output_dir
    else:
        config = load_config(args.config)
        output_dir = Path(
            os.getenv(
                "OUTPUT_DIR", config.get("download", {}).get("output_dir", "download")
            )
        )

    download_and_save(
        thingsboard_url=connection["thingsboard_url"],
        credentials=connection["credentials"],
        device_names=devices,
        start_time=start_time,
        end_time=end_time,
        output_dir=output_dir,
        variables=variables,
    )


if __name__ == "__main__":
    main()
