# Thingsboard download

This is a Python tool that enables users to download their data from Thingsboard as CSV files.

## Usage

The tool can be run via the command line. View the [`Installation`](#installation) instructions below for help with installing the required dependencies.

Credentials and download options can be configured in three different places.

1. A config file (by default, this uses the `config.toml` in the repository root)
2. Environment variables
3. Command-line arguments

For device download settings, command-line arguments override environment variables and the `config.toml`. For Thingsboard URL and authentication, values are loaded from environment variables or the `config.toml`.

### Config file

A minimal `config.toml` looks like this:

```toml
[thingsboard]
url = "https://example.com"

[auth]
# Use either your Thingsboard username/password...
username = "your.username@example.com"
password = "your-password"

# ...or an API key
# api_key = "your-api-key"

[download]
devices = ["DEVICE001", "DEVICE002"]
variables = ["temperature", "turbidity"]
start_time = "2026-08-01 09:00:00"
end_time = "2026-08-01 16:00:00"
output_dir = "output"

# Optional timeseries arguments passed through to get_timeseries
# interval = 60000
# limit = 500
# agg = "AVG"
```

Use this as a template and comment/uncomment code where appropriate.

### Environment variables

The following environment variables are supported:

- `THINGSBOARD_URL`
- `THINGSBOARD_USERNAME`
- `THINGSBOARD_PASSWORD`
- `THINGSBOARD_API_KEY`
- `DEVICES` as a comma-separated list, e.g., `DEVICES=DEVICE001,DEVICE002`
- `VARIABLES` as a comma-separated list, e.g., `VARIABLES=temperature,turbidity`
- `START_TIME` in `YYYY-MM-DD HH:MM:SS` format
- `END_TIME` in `YYYY-MM-DD HH:MM:SS` format
- `OUTPUT_DIR`
- `INTERVAL`
- `LIMIT`
- `AGG`

Note the following:

- You can provide either a username and password **or** an API key for authorization
- If `start_time` and `end_time` are both omitted, the tool downloads the last 30 days of data
- If `variables` are omitted, the tool requests all available timeseries keys for each device
- `interval`, `limit` and `agg` are all optional and will default to `None` if not provided

### Command-line options

The CLI supports the following options:

```text
-c, --config FILE       Path to the TOML configuration file
-d, --devices DEVICE    One or more device names
-v, --variables VAR     One or more variable names
-s, --start-time        Start time in YYYY-MM-DD HH:MM:SS format
-e, --end-time          End time in YYYY-MM-DD HH:MM:SS format
-o, --output-dir DIR    Output directory for CSV files
    --interval MS       Optional timeseries interval in milliseconds
    --limit N           Optional maximum number of data points
    --agg AGG           Optional aggregation type
```

### Running the tool

Run the tool from the repository root. If you are using `uv`:

```bash
uv sync
uv run python -m thingsboard_download
```

If you already have the dependencies installed in your active environment:

```bash
python -m thingsboard_download
```

Example using command-line arguments:

```bash
uv run python -m thingsboard_download \
  --devices SW-021 SW-022 \
  --variables fec turbidity \
  --start-time "2026-08-01 09:00:00" \
  --end-time "2026-08-01 16:00:00" \
  --output-dir output \
  --interval 60000 \
  --limit 500 \
  --agg AVG
```

`interval`, `limit`, and `agg` are all optional. By default they are left as `None` and are not given explicit values unless you set them via the config file, environment variables, or command-line arguments.

### Output

The tool writes one CSV file per device into the output directory, named as `DEVICE_NAME.csv` If the output directory already exists and is not empty, the tool asks for confirmation before continuing.

## Installation

To install:

1. [Download and install uv](https://docs.astral.sh/uv/getting-started/installation/) following the instructions for your OS.

1. Install the package and dependencies and set up the virtual environment:

    ```bash
    uv sync
    ```

1. Activate the virtual environment, or just preface your commands with `uv run` to use
the virtual environment (see [uv activate] for more info):

    ```bash
    source .venv/bin/activate
    <command>
    ```

    or

    ```bash
    uv run <command>
    ```

1. Run the main app:

    ```bash
    uv run python -m thingsboard_download
    ```
