# swe-physrag

Lightweight Python package for physics-informed data retrieval and interpolation.

## Overview

**physrag** combines:
- **Data Retrieval** — GEBCO bathymetry via OPeNDAP, CSV filtering by geographic/temporal extent
- **Spatial Interpolation** — 2D sparse data interpolation for point measurements
- **Simulation Integration** — Optional adapters for physics packages (e.g., tidalflow)

## Quick Start

### Installation
```bash
pip install -e .
```

### Usage
```python
import physrag

# Download bathymetry
df = physrag.bathymetry_retrieval.download_gebco_ascii(
    extent=(-87.23, -87.09, 30.20, 30.40)
)

# Filter CSV by extent
df = physrag.rag_data_retrieval.read_csv_extent(
    csv_path="data.csv",
    extent=(-87.23, -87.09, 30.20, 30.40),
    lat_col="latitude",
    lon_col="longitude"
)

# Interpolate sparse measurements
interp = physrag.data_interpolation.SparseDataInterpolator(x, y, values)
interpolated, uncertainty = interp.interpolate(x_grid, y_grid)
```

## Documentation

Complete documentation is in the `docs/` folder:

| Document | Purpose |
|----------|---------|
| [docs/index.md](docs/index.md) | Main API overview |
| [docs/getting-started.md](docs/getting-started.md) | Installation & basic usage |
| [docs/api.md](docs/api.md) | Complete API reference |
| [docs/architecture.md](docs/architecture.md) | Design principles & patterns |
| [docs/guides.md](docs/guides.md) | Usage examples & patterns |

## Features

✅ **Independent Core** — Use standalone without external package dependencies  
✅ **Optional Integrations** — Adapters for specific simulation packages  
✅ **Geospatial** — Extent-based filtering for geographic data  
✅ **Interpolation** — RBF-based 2D sparse data interpolation with uncertainty  
✅ **Remote Data Access** — Direct OPeNDAP access to GEBCO bathymetry  

## Project Structure

```
physrag/
├── bathymetry_retrieval/    # GEBCO data retrieval
├── data_interpolation/      # 2D sparse interpolation
├── rag_data_retrieval/      # CSV geospatial filtering
└── integrations/            # Optional package adapters
```

## Requirements

- Python >= 3.9
- numpy, pandas, scipy, requests

## Optional: tidalflow Integration

To use with tidalflow:

```bash
# Create conda environment
conda env create -f environment.yml
conda activate tidalflow

# Install tidalflow from source
git clone https://github.com/yourusername/TidalFlow-SWE.git
cd TidalFlow-SWE
pip install -r requirements.txt
pip install .

# Install physrag
cd /path/to/physrag
pip install -e .
```

Then use:
```python
from physrag.integrations.tidalflow_providers import (
    BathymetryFromGEBCO,
    WaterLevelInterpolationProvider,
)
```

See [docs/getting-started.md#using-with-tidalflow](docs/getting-started.md#using-with-tidalflow) for full instructions.

## Status

Early-stage package in active development. API subject to change.

## License

MIT

