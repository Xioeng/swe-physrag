"""
GEBCO data retrieval package.

Provides tools to:
1. Build OPeNDAP queries for GEBCO bathymetry data subsets using standard extent format
2. Download data via OPeNDAP and parse to pandas DataFrame
3. Optional persistence to CSV and temporary file management

**Usage Examples:**

Fast (in-memory, no disk output) with extent tuple (west, east, south, north):
    from physrag.bathymetry_retrieval import download_gebco_ascii
    df = download_gebco_ascii(extent=(-80.20, -80.06, 25.65, 25.93))
    print(df)

With CSV backup (optional):
    df = download_gebco_ascii(
        extent=(-80.20, -80.06, 25.65, 25.93),
        keep_csv=True
    )

Keep temporary ASCII file:
    df = download_gebco_ascii(
        extent=(-80.20, -80.06, 25.65, 25.93),
        keep_txt=True
    )

Chainable workflow - filter bathymetry by depth:
    df = download_gebco_ascii(extent=(-80.20, -80.06, 25.65, 25.93))
    print(df[df['Elevation'] < 0])  # Negative = underwater

Submodules:
- query: Build OPeNDAP query strings
- retrieval: Download data via OPeNDAP (returns DataFrame)
- conversion: Parse ASCII to DataFrame (optional CSV save)
"""

from .conversion import parse_gebco_ascii
from .query import build_query
from .retrieval import download_gebco_ascii, get_gebco_data

__all__ = ["build_query", "download_gebco_ascii", "get_gebco_data", "parse_gebco_ascii"]
