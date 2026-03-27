"""
RAG data retrieval package.

Provides tools to retrieve and filter geospatial data from various sources:
- CSV files with station/point measurements
- Bathymetry data (GEBCO) via OPeNDAP

**CSV Retrieval Features:**
- Filter by geographic extent (lat/lon bounding box)
- Flexible column mapping (specify which columns contain lat/lon/data)
- Optional temporal filtering
- Select specific columns to retrieve

**Usage Examples:**

Basic CSV filtering by extent (west, east, south, north):
    from physrag.rag_data_retrieval import read_csv_extent
    df = read_csv_extent(
        csv_path="data/weather.csv",
        extent=(-82.0, -80.0, 25.0, 30.0),
        lat_col="latitude_decimal_degrees",
        lon_col="longitude_decimal_degrees"
    )

Select specific columns:
    df = read_csv_extent(
        csv_path="data/weather.csv",
        extent=(-82.0, -80.0, 25.0, 30.0),
        lat_col="latitude_decimal_degrees",
        lon_col="longitude_decimal_degrees",
        columns=["station_name", "water_level_m_mllw", "wind_speed_m_per_s"]
    )

With temporal filtering:
    df = read_csv_extent(
        csv_path="data/weather.csv",
        extent=(-82.0, -80.0, 25.0, 30.0),
        lat_col="latitude_decimal_degrees",
        lon_col="longitude_decimal_degrees",
        timestamp_col="timestamp_utc_iso8601",
        start_time="2024-02-04T00:00:00Z",
        end_time="2024-02-05T00:00:00Z"
    )
"""

from .csv_retrieval import filter_by_extent, load_csv, read_csv_extent

__all__ = ["read_csv_extent", "filter_by_extent", "load_csv"]
