"""
CSV data retrieval module.

Reads and filters geospatial data from CSV files by geographic extent.
Supports flexible column mapping for varying data formats.
"""

from pathlib import Path

import pandas as pd

from physrag.utils import is_valid_extent


def load_csv(csv_path: str) -> pd.DataFrame:
    """
    Load CSV file into a pandas DataFrame.

    Args:
        csv_path (str): Path to the CSV file.

    Returns:
        pandas.DataFrame: Loaded CSV data.

    Raises:
        FileNotFoundError: If CSV file does not exist.
        pd.errors.ParserError: If CSV parsing fails.
    """
    # Convert to Path object for robust file handling
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Load CSV with pandas (handles various encodings and delimiters automatically)
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} records from: {csv_path}")

    return df


def filter_by_extent(
    df: pd.DataFrame,
    extent: tuple | list,
    lat_col: str = "latitude_decimal_degrees",
    lon_col: str = "longitude_decimal_degrees",
) -> pd.DataFrame:
    """
    Filter DataFrame records by geographic extent (bounding box).

    Args:
        df (pandas.DataFrame): Input data containing lat/lon columns.
        extent (tuple or list): Bounding box as (west, east, south, north).
            Follows Cartopy convention for geographic extents.
        lat_col (str): Name of the latitude column. Defaults to
            "latitude_decimal_degrees".
        lon_col (str): Name of the longitude column. Defaults to
            "longitude_decimal_degrees".

    Returns:
        pandas.DataFrame: Filtered data within the specified extent.

    Raises:
        ValueError: If extent format or coordinate bounds are invalid.
        KeyError: If specified column names don't exist in DataFrame.
    """
    # Validate extent format and unpack coordinates
    is_valid_extent(extent)
    west, east, south, north = extent

    # Validate that required columns exist
    if lat_col not in df.columns:
        raise KeyError(
            f"Latitude column '{lat_col}' not found in DataFrame. "
            f"Available columns: {list(df.columns)}"
        )
    if lon_col not in df.columns:
        raise KeyError(
            f"Longitude column '{lon_col}' not found in DataFrame. "
            f"Available columns: {list(df.columns)}"
        )

    # Apply geographic filtering (all conditions must be true)
    mask = (
        (df[lat_col] >= south)
        & (df[lat_col] <= north)
        & (df[lon_col] >= west)
        & (df[lon_col] <= east)
    )

    # Filter and report results
    filtered_df = df[mask].copy()
    print(
        f"Filtered to {len(filtered_df)} records within extent: "
        f"[W={west}°, E={east}°, S={south}°, N={north}°]"
    )

    return filtered_df


def read_csv_extent(
    csv_path: str,
    extent: tuple | list,
    lat_col: str = "latitude_decimal_degrees",
    lon_col: str = "longitude_decimal_degrees",
    columns: list[str] | None = None,
    timestamp_col: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> pd.DataFrame:
    """
    Read CSV file and filter records by geographic extent and optional time range.

    Combines loading, spatial filtering, and optional column/temporal selection
    into a single convenient call.

    Args:
        csv_path (str): Path to the CSV file.
        extent (tuple or list): Bounding box as (west, east, south, north).
            Follows Cartopy convention for geographic extents.
        lat_col (str): Name of the latitude column. Defaults to
            "latitude_decimal_degrees".
        lon_col (str): Name of the longitude column. Defaults to
            "longitude_decimal_degrees".
        columns (list[str]): Specific columns to retrieve. If None, returns all
            columns. Defaults to None.
        timestamp_col (str): Name of the timestamp column for temporal filtering.
            If None, temporal filtering is skipped. Defaults to None.
        start_time (str): Earliest timestamp (ISO8601 format). Only used if
            timestamp_col is specified. Defaults to None.
        end_time (str): Latest timestamp (ISO8601 format). Only used if
            timestamp_col is specified. Defaults to None.

    Returns:
        pandas.DataFrame: Filtered and selected data.

    Example:
        >>> df = read_csv_extent(
        ...     csv_path="weather_data.csv",
        ...     extent=(-82.0, -80.0, 25.0, 30.0),
        ...     lat_col="latitude_decimal_degrees",
        ...     lon_col="longitude_decimal_degrees",
        ...     columns=["station_name", "water_level_m_mllw", "wind_speed_m_per_s"],
        ...     timestamp_col="timestamp_utc_iso8601",
        ...     start_time="2024-02-04T00:00:00Z",
        ...     end_time="2024-02-05T00:00:00Z"
        ... )
    """
    # Load the CSV file
    df = load_csv(csv_path)

    # Apply geographic filtering using standard extent format (west, east, south, north)
    df = filter_by_extent(
        df,
        extent=extent,
        lat_col=lat_col,
        lon_col=lon_col,
    )

    # Optional: Apply temporal filtering if timestamp column specified
    if timestamp_col is not None:
        if timestamp_col not in df.columns:
            raise KeyError(
                f"Timestamp column '{timestamp_col}' not found in DataFrame. "
                f"Available columns: {list(df.columns)}"
            )

        # Convert timestamp column to datetime for comparison
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])

        # Apply time range filtering (if bounds provided)
        if start_time is not None:
            start_dt = pd.to_datetime(start_time)
            df = df[df[timestamp_col] >= start_dt]
            print(f"Filtered to records after: {start_time}")

        if end_time is not None:
            end_dt = pd.to_datetime(end_time)
            df = df[df[timestamp_col] <= end_dt]
            print(f"Filtered to records before: {end_time}")

        print(f"Time-filtered to {len(df)} records")

    # Optional: Select specific columns (include lat/lon/timestamp for reference)
    if columns is not None:
        # Ensure we always include the spatial coordinates
        columns_to_keep = list(set(columns + [lat_col, lon_col]))

        # Also keep timestamp if it was used for filtering
        if timestamp_col is not None:
            columns_to_keep = list(set(columns_to_keep + [timestamp_col]))

        # Filter to only available columns
        available_cols = [c for c in columns_to_keep if c in df.columns]
        df = df[available_cols]
        print(f"Selected {len(available_cols)} columns: {available_cols}")

    print(f"Final result: {len(df)} records × {len(df.columns)} columns")

    return df
