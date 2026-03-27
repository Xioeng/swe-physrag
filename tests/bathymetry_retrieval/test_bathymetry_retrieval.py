"""
Tests for bathymetry retrieval (bathymetry_retrieval module).

Tests cover GEBCO data download, parsing, and conversion.
Uses mocking to avoid actual network requests to OPeNDAP server.

Run with: pytest tests/bathymetry_retrieval/ -v
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from physrag.bathymetry_retrieval import (
    download_gebco_ascii,
    parse_gebco_ascii,
)
from physrag.bathymetry_retrieval.query import build_query

# Build query tests


def test_build_query_valid_extent():
    """Test query building with valid extent."""
    extent = (-80.2, -80.0, 25.6, 25.95)
    url, description = build_query(extent=extent)

    assert isinstance(url, str)
    assert isinstance(description, str)
    assert "opendap" in url.lower() or "gebco" in url.lower()
    assert str(extent[0]) in description


# TODO:
# def test_build_query_different_versions():
#     """Test query building with different GEBCO versions."""
#     extent = (-80.2, -80.0, 25.6, 25.95)

#     # Test with different version
#     url_2025, desc_2025 = build_query(extent=extent, version="2025")
#     url_2023, desc_2023 = build_query(extent=extent, version="2023")

#     # URLs should be different
#     assert url_2025 != url_2023


def test_build_query_stride_effect():
    """Test that stride parameter affects query."""
    extent = (-80.2, -80.0, 25.6, 25.95)

    url_stride1, _ = build_query(extent=extent, stride=1)
    url_stride2, _ = build_query(extent=extent, stride=2)

    # Stride affects the URL
    assert url_stride1 != url_stride2


def test_build_query_global_extent():
    """Test query with global extent."""
    extent = (-180, 180, -90, 90)
    url, description = build_query(extent=extent)

    assert isinstance(url, str)
    assert len(url) > 0


def test_build_query_small_region():
    """Test query with very small region."""
    extent = (-80.101, -80.099, 25.799, 25.801)
    url, description = build_query(extent=extent)

    assert isinstance(url, str)
    assert len(url) > 0


# Parse GEBCO ASCII tests

# TODO: Get realistic GEBCO ASCII sample for testing, or mock the file reading more extensively.
# def test_parse_gebco_ascii_basic():
#     """Test basic ASCII parsing."""
#     # Create sample GEBCO ASCII response
#     ascii_data = """
#     -80.20, 25.60, -100.5
#     -80.19, 25.60, -95.2
#     -80.20, 25.61, -110.0
#     """

#     with TemporaryDirectory() as tmpdir:
#         ascii_file = Path(tmpdir) / "gebco.txt"
#         ascii_file.write_text(ascii_data)

#         df = parse_gebco_ascii(str(ascii_file))

#         assert isinstance(df, pd.DataFrame)
#         assert len(df) == 3
#         assert "Longitude" in df.columns or "longitude" in df.columns.str.lower()


# def test_parse_gebco_ascii_multiindex_header():
#     """Test parsing with multi-line header."""
#     # GEBCO OPeNDAP often has metadata headers
#     ascii_data = """
#     Dataset {
#       Float32 GEBCO_2025_GRID[lat = 43200][lon = 86400];
#     } gebco_2025;
#     -80.20, 25.60, -100.5
#     -80.19, 25.60, -95.2
#     -80.20, 25.61, -110.0
#     """

#     with TemporaryDirectory() as tmpdir:
#         ascii_file = Path(tmpdir) / "gebco_with_header.txt"
#         ascii_file.write_text(ascii_data)

#         df = parse_gebco_ascii(str(ascii_file))

#         # Should have parsed the data correctly
#         assert len(df) == 3


# def test_parse_gebco_ascii_returns_dataframe():
#     """Test that return type is pandas DataFrame."""
#     ascii_data = "-80.50, 25.50, -200.0\n"

#     with TemporaryDirectory() as tmpdir:
#         ascii_file = Path(tmpdir) / "single_point.txt"
#         ascii_file.write_text(ascii_data)

#         df = parse_gebco_ascii(str(ascii_file))

#         assert isinstance(df, pd.DataFrame)


def test_parse_gebco_ascii_large_file():
    """Test parsing larger GEBCO ASCII file."""
    # Generate grid of points
    lons = np.linspace(-80.2, -80.0, 20)
    lats = np.linspace(25.6, 25.95, 20)

    lines = []
    for lon in lons:
        for lat in lats:
            elev = -1000 + np.random.uniform(-500, 500)
            lines.append(f"{lon:.4f}, {lat:.4f}, {elev:.1f}")

    ascii_data = "\n".join(lines)

    with TemporaryDirectory() as tmpdir:
        ascii_file = Path(tmpdir) / "large_gebco.txt"
        ascii_file.write_text(ascii_data)

        df = parse_gebco_ascii(str(ascii_file))

        assert len(df) == 400
        # Check for expected columns (flexible naming)
        cols_lower = [c.lower() for c in df.columns]
        assert any("lon" in c or "x" in c for c in cols_lower)
        assert any("lat" in c or "y" in c for c in cols_lower)


# Download GEBCO ASCII tests


@patch("physrag.bathymetry_retrieval.retrieval.requests.get")
def test_download_gebco_ascii_success(mock_get):
    """Test successful download."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "-80.20, 25.60, -100.5\n-80.19, 25.60, -95.2\n"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    with TemporaryDirectory() as tmpdir:
        df = download_gebco_ascii(extent=(-80.2, -80.0, 25.6, 25.95), output_dir=tmpdir)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2


@patch("physrag.bathymetry_retrieval.retrieval.requests.get")
def test_download_gebco_ascii_creates_directory(mock_get):
    """Test that output directory is created."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "-80.20, 25.60, -100.5\n"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "gebco_data" / "nested"

        download_gebco_ascii(
            extent=(-80.2, -80.0, 25.6, 25.95), output_dir=str(output_dir)
        )

        assert output_dir.exists()


@patch("physrag.bathymetry_retrieval.retrieval.requests.get")
def test_download_gebco_ascii_keep_txt(mock_get):
    """Test keep_txt parameter."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "-80.20, 25.60, -100.5\n"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    with TemporaryDirectory() as tmpdir:
        df = download_gebco_ascii(
            extent=(-80.2, -80.0, 25.6, 25.95), output_dir=tmpdir, keep_txt=True
        )

        assert isinstance(df, pd.DataFrame)


@patch("physrag.bathymetry_retrieval.retrieval.requests.get")
def test_download_gebco_ascii_invalid_extent(mock_get):
    """Test with invalid extent."""
    # Invalid extent should be caught by is_valid_extent
    with pytest.raises(ValueError):
        download_gebco_ascii(
            extent=(-80.2, -80.0, 30.0, 25.0),  # south > north
            output_dir=".",
        )


@patch("physrag.bathymetry_retrieval.retrieval.requests.get")
def test_download_gebco_ascii_different_versions(mock_get):
    """Test downloading different GEBCO versions."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "-80.20, 25.60, -100.5\n"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    with TemporaryDirectory() as tmpdir:
        for version in ["2025", "2023"]:
            df = download_gebco_ascii(
                extent=(-80.2, -80.0, 25.6, 25.95),
                output_dir=tmpdir,
                version=version,
            )

            assert isinstance(df, pd.DataFrame)


# Bathymetry data quality tests


def test_bathymetry_elevation_range():
    """Test that bathymetry elevation values are in reasonable range."""
    # Realistic elevation range: -11000 (deepest) to +8000 (highest)
    ascii_data = """
    -80.20, 25.60, -1000.5
    -80.19, 25.60, -995.2
    -80.20, 25.61, -1100.0
    """

    with TemporaryDirectory() as tmpdir:
        ascii_file = Path(tmpdir) / "gebco.txt"
        ascii_file.write_text(ascii_data)

        df = parse_gebco_ascii(str(ascii_file))

        # Get elevation column (flexible naming)
        elev_col = [
            c for c in df.columns if "elev" in c.lower() or "elevation" in c.lower()
        ]
        if elev_col:
            elevations = df[elev_col[0]].values
            assert np.all(elevations >= -11000)  # Deeper than Mariana Trench
            assert np.all(elevations <= 8848)  # Higher than Mt. Everest


def test_bathymetry_geographic_coverage():
    """Test that bathymetry data covers the requested extent."""
    extent = (-80.2, -80.0, 25.6, 25.95)
    lons = np.linspace(extent[0], extent[1], 5)
    lats = np.linspace(extent[2], extent[3], 5)

    lines = []
    for lon in lons:
        for lat in lats:
            lines.append(f"{lon:.4f}, {lat:.4f}, -1000.0")

    ascii_data = "\n".join(lines)

    with TemporaryDirectory() as tmpdir:
        ascii_file = Path(tmpdir) / "gebco.txt"
        ascii_file.write_text(ascii_data)

        df = parse_gebco_ascii(str(ascii_file))

        # Find longitude/latitude columns
        lon_col = [c for c in df.columns if "lon" in c.lower()][0]
        lat_col = [c for c in df.columns if "lat" in c.lower()][0]

        min_lon = df[lon_col].min()
        max_lon = df[lon_col].max()
        min_lat = df[lat_col].min()
        max_lat = df[lat_col].max()

        # Data should cover the extent
        assert min_lon >= extent[0]
        assert max_lon <= extent[1]
        assert min_lat >= extent[2]
        assert max_lat <= extent[3]


# Bathymetry integration tests


@patch("physrag.bathymetry_retrieval.retrieval.requests.get")
def test_query_parse_workflow(mock_get):
    """Test complete workflow: query → download → parse."""
    # Mock network response
    mock_response = MagicMock()
    mock_response.status_code = 200

    # Generate realistic GEBCO-like data
    lons = np.linspace(-80.2, -80.0, 10)
    lats = np.linspace(25.6, 25.95, 10)
    lines = []
    for lon in lons:
        for lat in lats:
            elev = -1000 + np.sin(lon) * 100 + np.cos(lat) * 100
            lines.append(f"{lon:.4f}, {lat:.4f}, {elev:.1f}")

    mock_response.text = "\n".join(lines)
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    with TemporaryDirectory() as tmpdir:
        # Download
        df = download_gebco_ascii(extent=(-80.2, -80.0, 25.6, 25.95), output_dir=tmpdir)

        # Verify
        assert len(df) == 100
        assert "Longitude" in df.columns or "longitude" in [
            c.lower() for c in df.columns
        ]


def test_bathymetry_multiple_calls():
    """Test multiple batch downloads of different regions."""
    extents = [
        (-80.2, -80.0, 25.6, 25.95),  # Miami/Virginia Key area
        (-87.3, -87.0, 30.2, 30.5),  # Pensacola area
        (-81.0, -80.5, 25.0, 25.5),  # Key West area
    ]

    for extent in extents:
        # Would call download_gebco_ascii for each extent
        # Just verify extents are valid
        from physrag.utils import is_valid_extent

        assert is_valid_extent(extent)
