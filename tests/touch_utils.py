"""Tests for utils.py."""

import pandas as pd

from thingsboard_download.utils import process_downloaded_data


def test_process_downloaded_data():
    """Test the process_downloaded_data function."""
    data = {
        "turbidity": [
            {"ts": 1785595829000, "value": 0.5},
            {"ts": 1785595830000, "value": 0.7},
            {"ts": 1785595831000, "value": 0.9},
        ],
        "fec": [
            {"ts": 1785595829000, "value": 1.5},
            {"ts": 1785595830000, "value": 1.7},
            {"ts": 1785595831000, "value": 1.9},
        ],
    }

    expected_df = pd.DataFrame(
        {
            "time": pd.to_datetime(
                pd.Series([1785595829000, 1785595830000, 1785595831000]), unit="ms"
            ),
            "turbidity": [0.5, 0.7, 0.9],
            "fec": [1.5, 1.7, 1.9],
        }
    )
    expected_df = expected_df.set_index("time").rename_axis(None)
    df = process_downloaded_data(data, ["turbidity", "fec"])
    pd.testing.assert_frame_equal(expected_df, df)
