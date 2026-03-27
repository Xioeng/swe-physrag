# physrag API Documentation

**physrag** (Physical Retrieval-Augmented Generation) — A data retrieval and interpolation library for physics simulations.

## Overview

physrag provides:
- **Bathymetry Data Retrieval** — Download GEBCO bathymetry via OPeNDAP
- **Spatial Data Filtering** — Filter CSV/geospatial data by geographic extent
- **Sparse Data Interpolation** — Interpolate and extrapolate from point measurements
- **Simulation Integrations** — Optional adapters for physics simulation packages (e.g., tidalflow)

## Quick Start

### Installation (Core Only)
```bash
pip install -e .
```

### Basic Usage
```python
import physrag

# Download bathymetry
df = physrag.bathymetry_retrieval.download_gebco_ascii(
    extent=(-87.23, -87.09, 30.20, 30.40)
)

# Read local data with spatial filtering
df = physrag.rag_data_retrieval.read_csv_extent(
    csv_path="data.csv",
    extent=(-87.23, -87.09, 30.20, 30.40),
    lat_col="latitude",
    lon_col="longitude"
)

# Interpolate sparse measurements
interp = physrag.data_interpolation.SparseDataInterpolator(
    x=df['lon'].values,
    y=df['lat'].values,
    values=df['water_level'].values
)
interpolated, uncertainty = interp.interpolate(lon_grid, lat_grid)
```

## Core Modules

### physrag.bathymetry_retrieval
Download and process GEBCO bathymetry data via OPeNDAP.

**Key Functions:**
- `download_gebco_ascii(extent, keep_csv, keep_txt)` — Download GEBCO data for geographic extent
- `get_gebco_data(extent, keep_csv, keep_txt)` — Combined retrieval and conversion

**Extent Format:** `(west, east, south, north)` in lon/lat coordinates

### physrag.rag_data_retrieval
Filter and process geospatial data from CSV files.

**Key Functions:**
- `read_csv_extent(csv_path, extent, lat_col, lon_col, columns, timestamp_col, ...)` — Load and filter CSV by geographic extent
- `filter_by_extent(df, extent, lat_col, lon_col)` — Filter existing DataFrame
- `load_csv(csv_path, columns, timestamp_col, ...)` — Load CSV with optional filtering

### physrag.data_interpolation
Interpolate and extrapolate from sparse point measurements.

**Key Classes:**
- `SparseDataInterpolator(x, y, values)` — Interpolator for 2D sparse data
  - `interpolate(x_new, y_new)` — Returns (interpolated_values, uncertainties)

## Optional Integrations

### physrag.integrations.tidalflow_providers
Adapters for integrating physrag data with tidalflow.

**Requires:** tidalflow installed in conda environment

**Key Classes:**
- `BathymetryFromGEBCO(extent, keep_csv, csv_path)` — Bathymetry provider for tidalflow
- `WaterLevelInterpolationProvider(lon, lat, values)` — Water level provider for tidalflow

**See:** [Getting Started with tidalflow](./getting-started.md#using-with-tidalflow)

## Documentation Index

| Document | Purpose |
|----------|---------|
| [Getting Started](./getting-started.md) | Installation & basic usage |
| [API Reference](./api.md) | Complete module & class reference |
| [Architecture](./architecture.md) | Design principles & design patterns |
| [Guides](./guides.md) | Usage patterns & examples |

## Project Structure

```
physrag/
├── bathymetry_retrieval/    # GEBCO OPeNDAP data retrieval
├── data_interpolation/       # 2D sparse data interpolation
├── rag_data_retrieval/       # CSV geospatial filtering
└── integrations/             # Optional package adapters
    └── tidalflow_providers.py
```

## Dependencies

**Core (always required):**
- numpy >= 1.21.0
- pandas >= 1.3.0
- scipy >= 1.7.0
- requests >= 2.26.0

**Optional (for integrations):**
- tidalflow (requires conda environment setup)

**Development:**
- pytest, black, mypy, flake8, isort

## Key Features

✅ **Independent Core** — Use physrag standalone without external package dependencies  
✅ **Optional Integrations** — Adapters for specific simulation packages  
✅ **Geospatial** — Built-in extent/filtering for geographic data  
✅ **Interpolation** — Sparse to dense data interpolation with uncertainty estimates  
✅ **Remote Data** — Direct OPeNDAP access to public bathymetry datasets  

## Configuration & Installation

For installation variations, see [Getting Started](./getting-started.md).

For detailed architecture and design patterns, see [Architecture Guide](./architecture.md).
