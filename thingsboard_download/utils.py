"""Utils module."""

import pandas as pd


def process_downloaded_data(
    data: dict[str, list[dict[str, int | float | str]]], variables: list[str]
) -> pd.DataFrame:
    """Process the downloaded data into a dictionary of dictionaries.

    Args:
        data: The downloaded data.
        variables: The list of variables to include in the dataframe.

    Returns:
        A Pandas dataframe containing the processed data.
    """
    df_data = {var: {} for var in variables}
    for variable, measurements in data.items():
        for measurement in measurements:
            time = measurement["ts"]
            value = measurement["value"]
            df_data[variable][time] = value

    df = pd.DataFrame(df_data)
    df.index = pd.to_datetime(df.index, unit="ms")
    df.index = df.index.sort_values()
    return df
