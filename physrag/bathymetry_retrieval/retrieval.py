"""
GEBCO data retrieval module.

Downloads GEBCO bathymetry data via CEDA OPeNDAP ASCII endpoint.
Optionally cleans up temporary ASCII files.
"""

from pathlib import Path

import pandas as pd
import requests

from .conversion import parse_gebco_ascii
from .query import build_query


def download_gebco_ascii(
    extent: tuple | list,
    output_dir: str = "gebco_data",
    version: str = "2025",
    stride: int = 1,
    keep_txt: bool = False,
) -> pd.DataFrame:
    """
    Download GEBCO bathymetry data via CEDA OPeNDAP ASCII endpoint.

    Fetches bathymetry data for a geographic extent, parses the OPeNDAP ASCII
    response into a pandas DataFrame, and optionally manages temporary files.

    Args:
        extent (tuple or list): Bounding box as (west, east, south, north).
            Follows Cartopy convention for geographic extents.
        output_dir (str): Directory to save temporary files. Defaults to "gebco_data".
        version (str): GEBCO version string (e.g., "2025"). Defaults to "2025".
        stride (int): Sampling stride; 1 = every point, 2 = every other point, etc.
            Defaults to 1.
        keep_txt (bool): If True, keep the ASCII .txt file; if False, delete after
            parsing. Defaults to False (clean up automatically).

    Returns:
        pandas.DataFrame: Data with columns [Longitude, Latitude, Elevation].

    Raises:
        ValueError: If extent format or coordinate bounds are invalid.
        requests.RequestException: If OPeNDAP request fails.
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Unpack extent for filename generation
    west, east, south, north = extent

    # Build the OPeNDAP query URL with coordinate->index conversion
    url, description = build_query(extent=extent, stride=stride)

    print(f"Query: {description}")
    print("Fetching data from OPeNDAP...")

    # Fetch the ASCII response from the OPeNDAP server
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # Write raw ASCII response to temporary file
    filename = f"gebco_{version}_n{north}_s{south}_w{west}_e{east}.txt"
    filepath = Path(output_dir) / filename
    with open(filepath, "w") as f:
        f.write(response.text)
    print(f"Downloaded ASCII response to: {filepath}")

    # Parse the ASCII file into a pandas DataFrame
    df = parse_gebco_ascii(str(filepath))

    # Optionally delete temporary ASCII file (default: clean up automatically)
    if not keep_txt:
        filepath.unlink()
        print(f"Deleted temporary ASCII file: {filepath}")

    return df


def get_gebco_data(
    extent: tuple | list,
    output_dir: str = "gebco_data",
    version: str = "2025",
    stride: int = 1,
    keep_txt: bool = True,
    keep_csv: bool = False,
) -> tuple[pd.DataFrame, str | None, str | None]:
    """
    Download GEBCO data with explicit control over file retention.

    Higher-level wrapper around download_gebco_ascii that provides explicit
    control over whether to keep temporary ASCII or generate CSV files.

    Args:
        extent (tuple or list): Bounding box as (west, east, south, north).
            Follows Cartopy convention for geographic extents.
        output_dir (str): Directory to save files. Defaults to "gebco_data".
        version (str): GEBCO version string. Defaults to "2025".
        stride (int): Sampling stride. Defaults to 1.
        keep_txt (bool): If True, retain ASCII .txt file; if False, delete after parsing.
            Defaults to True.
        keep_csv (bool): If True, save a CSV export of the data.
            Defaults to False.

    Returns:
        tuple: (df, txt_filepath_or_None, csv_filepath_or_None)
    """
    west, east, south, north = extent
    txt_path = Path(output_dir) / f"gebco_{version}_n{north}_s{south}_w{west}_e{east}.txt"

    # Download and parse data directly
    df = download_gebco_ascii(
        extent=extent,
        output_dir=output_dir,
        version=version,
        stride=stride,
        keep_txt=keep_txt,
    )

    csv_filepath = None
    # Optionally save CSV export (if CSV desired, save directly from DataFrame)
    if keep_csv:
        csv_filepath = (
            Path(output_dir) / f"gebco_{version}_w{west}_e{east}_s{south}_n{north}.csv"
        )
        df.to_csv(csv_filepath, index=False)
        print(f"Saved CSV to: {csv_filepath}")

    return (
        df,
        str(txt_path) if keep_txt else None,
        str(csv_filepath) if keep_csv else None,
    )
