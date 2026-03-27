"""
Tests for CSV data retrieval (csv_retrieval module).

Tests cover loading CSV files and filtering by geographic extent.

Run with: pytest tests/rag_data_retrieval/test_csv_retrieval.py -v
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
import pytest

from physrag.rag_data_retrieval import (
    filter_by_extent,
    load_csv,
    read_csv_extent,
)


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file with sample data."""
    with TemporaryDirectory() as tmpdir:
        # Create sample data
        data = {
            "longitude_decimal_degrees": [-80.19, -80.13, -80.10, -80.05],
            "latitude_decimal_degrees": [25.76, 26.12, 25.80, 25.90],
            "water_level_m": [0.5, 0.8, 0.3, 0.6],
            "temperature_c": [28.5, 27.8, 28.0, 28.2],
        }
        df = pd.DataFrame(data)

        csv_path = Path(tmpdir) / "test_data.csv"
        df.to_csv(csv_path, index=False)

        yield csv_path, df


@pytest.fixture
def temp_large_csv_file():
    """Create a larger temporary CSV file with more varied data."""
    with TemporaryDirectory() as tmpdir:
        # Create grid of points across Florida
        lon = np.linspace(-87.6, -80.0, 20)
        lat = np.linspace(24.5, 30.8, 20)

        data = {
            "station_id": [f"STATION_{i}" for i in range(400)],
            "longitude": np.repeat(lon, 20),
            "latitude": np.tile(lat, 20),
            "water_level": np.random.uniform(0, 2, 400),
            "temperature": np.random.uniform(20, 30, 400),
        }
        df = pd.DataFrame(data)

        csv_path = Path(tmpdir) / "large_data.csv"
        df.to_csv(csv_path, index=False)

        yield csv_path, df


# CSV loading tests


def test_load_csv_basic(temp_csv_file):
    """Test basic CSV loading."""
    csv_path, expected_df = temp_csv_file

    df = load_csv(csv_path)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 4
    assert list(df.columns) == [
        "longitude_decimal_degrees",
        "latitude_decimal_degrees",
        "water_level_m",
        "temperature_c",
    ]


def test_load_csv_data_integrity(temp_csv_file):
    """Test that loaded data matches original."""
    csv_path, expected_df = temp_csv_file

    df = load_csv(csv_path)

    pd.testing.assert_frame_equal(df, expected_df)


def test_load_csv_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError, match="not found"):
        load_csv("nonexistent_file.csv")


def test_load_csv_preserves_dtypes(temp_csv_file):
    """Test that data types are preserved."""
    csv_path, _ = temp_csv_file

    df = load_csv(csv_path)

    # String columns should be object dtype
    assert df["longitude_decimal_degrees"].dtype in [np.float64, float]
    assert df["latitude_decimal_degrees"].dtype in [np.float64, float]


def test_load_csv_with_missing_values():
    """Test loading CSV with missing values."""
    with TemporaryDirectory() as tmpdir:
        # Create data with NaN
        data = {
            "lon": [-80.1, -80.2, None],
            "lat": [25.8, None, 25.9],
            "value": [1.0, 2.0, 3.0],
        }
        df_orig = pd.DataFrame(data)

        csv_path = Path(tmpdir) / "with_nan.csv"
        df_orig.to_csv(csv_path, index=False)

        df = load_csv(csv_path)

        assert df.isna().sum().sum() > 0  # Should have NaN values


# Extent filtering tests


def test_filter_by_extent_basic(temp_csv_file):
    """Test basic extent filtering."""
    csv_path, _ = temp_csv_file
    df = load_csv(csv_path)

    # Filter to small extent
    extent = (-80.15, -80.10, 25.75, 26.15)
    filtered = filter_by_extent(
        df,
        extent,
        lat_col="latitude_decimal_degrees",
        lon_col="longitude_decimal_degrees",
    )

    # Should have some points
    assert len(filtered) > 0
    assert len(filtered) <= len(df)


def test_filter_by_extent_bounds(temp_csv_file):
    """Test that all filtered points are within extent."""
    csv_path, _ = temp_csv_file
    df = load_csv(csv_path)

    extent = (-80.15, -80.10, 25.80, 26.12)
    filtered = filter_by_extent(
        df,
        extent,
        lat_col="latitude_decimal_degrees",
        lon_col="longitude_decimal_degrees",
    )

    # All points should be within bounds
    assert np.all(filtered["longitude_decimal_degrees"] >= extent[0])
    assert np.all(filtered["longitude_decimal_degrees"] <= extent[1])
    assert np.all(filtered["latitude_decimal_degrees"] >= extent[2])
    assert np.all(filtered["latitude_decimal_degrees"] <= extent[3])


def test_filter_by_extent_empty_result(temp_csv_file):
    """Test filtering that results in no points."""
    csv_path, _ = temp_csv_file
    df = load_csv(csv_path)

    # Extent with no data
    extent = (-81.0, -80.9, 27.0, 27.5)
    filtered = filter_by_extent(
        df,
        extent,
        lat_col="latitude_decimal_degrees",
        lon_col="longitude_decimal_degrees",
    )

    assert len(filtered) == 0


def test_filter_by_extent_all_points(temp_csv_file):
    """Test filtering with extent containing all points."""
    csv_path, _ = temp_csv_file
    df = load_csv(csv_path)

    # Large extent containing all points
    extent = (-90, -70, 20, 30)
    filtered = filter_by_extent(
        df,
        extent,
        lat_col="latitude_decimal_degrees",
        lon_col="longitude_decimal_degrees",
    )

    assert len(filtered) == len(df)


def test_filter_by_extent_custom_columns():
    """Test filtering with non-standard column names."""
    with TemporaryDirectory() as tmpdir:
        data = {
            "x": [-80.1, -80.2, -80.0],
            "y": [25.8, 25.9, 26.0],
            "data": [1.0, 2.0, 3.0],
        }
        df = pd.DataFrame(data)

        csv_path = Path(tmpdir) / "custom_cols.csv"
        df.to_csv(csv_path, index=False)

        loaded = load_csv(csv_path)

        extent = (-80.15, -80.05, 25.75, 25.95)
        filtered = filter_by_extent(loaded, extent, lat_col="y", lon_col="x")

        assert len(filtered) > 0


def test_filter_by_extent_on_boundary(temp_csv_file):
    """Test filtering when extent boundary matches point."""
    csv_path, _ = temp_csv_file
    df = load_csv(csv_path)

    # Point at -80.19, 25.76
    extent = (-80.19, -80.13, 25.76, 26.12)
    filtered = filter_by_extent(
        df,
        extent,
        lat_col="latitude_decimal_degrees",
        lon_col="longitude_decimal_degrees",
    )

    # Should include boundary point
    assert len(filtered) >= 1


# Integrated CSV extent reading tests


def test_read_csv_extent_basic(temp_csv_file):
    """Test basic read_csv_extent."""
    csv_path, _ = temp_csv_file

    extent = (-80.15, -80.10, 25.80, 26.12)
    df = read_csv_extent(
        str(csv_path),
        extent,
        lat_col="latitude_decimal_degrees",
        lon_col="longitude_decimal_degrees",
    )

    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0


def test_read_csv_extent_preserves_columns(temp_csv_file):
    """Test that all columns are preserved."""
    csv_path, _ = temp_csv_file

    extent = (-80.15, -80.10, 25.75, 26.15)
    df = read_csv_extent(
        str(csv_path),
        extent,
        lat_col="latitude_decimal_degrees",
        lon_col="longitude_decimal_degrees",
    )

    expected_cols = [
        "longitude_decimal_degrees",
        "latitude_decimal_degrees",
        "water_level_m",
        "temperature_c",
    ]
    assert list(df.columns) == expected_cols


def test_read_csv_extent_with_large_file(temp_large_csv_file):
    """Test with larger CSV file."""
    csv_path, _ = temp_large_csv_file

    extent = (-86, -81, 25, 30)
    df = read_csv_extent(str(csv_path), extent, lat_col="latitude", lon_col="longitude")

    assert len(df) > 0
    assert len(df) <= 400


def test_read_csv_extent_file_not_found():
    """Test that FileNotFoundError is raised."""
    with pytest.raises(FileNotFoundError):
        read_csv_extent(
            "nonexistent.csv",
            (-80.2, -80.0, 25.6, 26.0),
            lat_col="lat",
            lon_col="lon",
        )


def test_read_csv_extent_missing_column(temp_csv_file):
    """Test that KeyError is raised when column doesn't exist."""
    csv_path, _ = temp_csv_file

    with pytest.raises(KeyError):
        read_csv_extent(
            str(csv_path),
            (-80.2, -80.0, 25.6, 26.0),
            lat_col="nonexistent_lat",
            lon_col="longitude_decimal_degrees",
        )


def test_read_csv_extent_with_selected_columns(temp_csv_file):
    """Test reading with only selected columns."""
    csv_path, _ = temp_csv_file

    extent = (-80.15, -80.10, 25.75, 26.15)
    df = read_csv_extent(
        str(csv_path),
        extent,
        lat_col="latitude_decimal_degrees",
        lon_col="longitude_decimal_degrees",
        columns=[
            "longitude_decimal_degrees",
            "latitude_decimal_degrees",
            "water_level_m",
        ],
    )

    expected_cols = [
        "longitude_decimal_degrees",
        "latitude_decimal_degrees",
        "water_level_m",
    ]
    assert list(df.columns) == expected_cols


def test_read_csv_extent_with_timestamp_filtering():
    """Test temporal filtering with timestamps."""
    with TemporaryDirectory() as tmpdir:
        # Create data with timestamps
        data = {
            "lon": [-80.1, -80.1, -80.1],
            "lat": [25.8, 25.8, 25.8],
            "timestamp": ["2024-01-01", "2024-02-01", "2024-03-01"],
            "value": [1.0, 2.0, 3.0],
        }
        df_orig = pd.DataFrame(data)

        csv_path = Path(tmpdir) / "time_data.csv"
        df_orig.to_csv(csv_path, index=False)

        df = read_csv_extent(
            str(csv_path),
            (-80.2, -80.0, 25.7, 25.9),
            lat_col="lat",
            lon_col="lon",
            timestamp_col="timestamp",
            start_time="2024-01-15",
            end_time="2024-02-15",
        )

        # Should have 1 point (Feb 1)
        assert len(df) == 1


# CSV retrieval integration tests


def test_workflow_download_filter_analyze(temp_large_csv_file):
    """Test typical workflow: load → filter → analyze."""
    csv_path, original_df = temp_large_csv_file

    # Load
    df = load_csv(str(csv_path))
    assert len(df) == len(original_df)

    # Filter
    extent = (-85, -81, 25, 30)
    filtered = read_csv_extent(
        str(csv_path), extent, lat_col="latitude", lon_col="longitude"
    )
    assert len(filtered) > 0
    assert len(filtered) < len(df)

    # Analyze
    assert "water_level" in filtered.columns
    assert filtered["water_level"].mean() >= 0
