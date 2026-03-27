# Getting Started

## Installation

### Core Installation (Recommended)
```bash
cd /path/to/physrag
pip install -e .
```

**What's installed:**
- physrag core modules (bathymetry_retrieval, data_interpolation, rag_data_retrieval)
- Dependencies: numpy, pandas, scipy, requests
- Ready to use immediately

**Verification:**
```bash
python -c "import physrag; print(physrag.__file__)"
```

### Development Installation
```bash
pip install -e ".[dev]"
```

**Adds:** pytest, black, mypy, flake8, isort

### Full Installation (All Extras)
```bash
pip install -e ".[all]"
```

**Adds:** dev tools + documentation tools

---

## Using with tidalflow

⚠️ **Special Setup Required** — tidalflow requires conda environment management.

### Prerequisites
- tidalflow must be installed in conda environment
- Cannot be installed via pip extras

### Setup Steps

**1. Create conda environment**
```bash
conda env create -f environment.yml
conda activate tidalflow
```

**2. Install tidalflow from source**
```bash
git clone https://github.com/yourusername/TidalFlow-SWE.git
cd TidalFlow-SWE
pip install -r requirements.txt
pip install .
```

**3. Install physrag in same environment**
```bash
cd /path/to/physrag
pip install -e .
```

### Usage
```bash
# Always activate conda environment first
conda activate tidalflow

# Now use physrag with tidalflow
python your_script.py
```

**Verification:**
```bash
conda activate tidalflow
python -c "from physrag.integrations.tidalflow_providers import BathymetryFromGEBCO; print('OK')"
```

---

## Basic Usage Examples

### Download Bathymetry Data
```python
import physrag

extent = (-87.23, -87.09, 30.20, 30.40)  # (west, east, south, north)

# Direct download
df = physrag.bathymetry_retrieval.download_gebco_ascii(extent=extent)
print(df.head())
```

### Filter CSV by Geographic Extent
```python
import physrag

extent = (-87.23, -87.09, 30.20, 30.40)

df = physrag.rag_data_retrieval.read_csv_extent(
    csv_path="weather_data.csv",
    extent=extent,
    lat_col="latitude_decimal_degrees",
    lon_col="longitude_decimal_degrees",
    columns=["station_name", "water_level_m_mllw", "temperature_c"]
)
print(f"Found {len(df)} stations in extent")
```

### Interpolate Sparse Measurements
```python
import physrag
import numpy as np

# Your measurement data
lons = np.array([-87.2, -87.1, -87.15])
lats = np.array([30.3, 30.35, 30.25])
values = np.array([1.2, 0.8, 1.0])  # water levels

# Create interpolator
interp = physrag.data_interpolation.SparseDataInterpolator(
    x=lons,
    y=lats,
    values=values
)

# Interpolate on regular grid
lon_grid, lat_grid = np.meshgrid(
    np.linspace(-87.25, -87.05, 50),
    np.linspace(30.2, 30.4, 50)
)
interpolated, uncertainties = interp.interpolate(
    lon_grid.flatten(),
    lat_grid.flatten()
)

print(interpolated.reshape(lon_grid.shape))
```

### With tidalflow Integration
```python
from physrag.integrations.tidalflow_providers import (
    BathymetryFromGEBCO,
    WaterLevelInterpolationProvider,
)
import tidalflow
import numpy as np

extent = (-87.23, -87.09, 30.20, 30.40)

# Create providers using physrag
bath_provider = BathymetryFromGEBCO(extent=extent)
water_provider = WaterLevelInterpolationProvider(
    lon=np.array([-87.2, -87.1, -87.15]),
    lat=np.array([30.3, 30.35, 30.25]),
    values=np.array([1.2, 0.8, 1.0])
)

# Use with tidalflow
config = tidalflow.config.SimulationConfig(
    lon_range=(extent[0], extent[1]),
    lat_range=(extent[2], extent[3]),
    nx=40, ny=40,
    t_final=1000.0,
    dt=1.0,
)

solver = tidalflow.solver.SWESolver(
    config=config,
    bathymetry_provider=bath_provider,
    ic_provider=water_provider,
)

solver.initialize_data_from_providers()
result = solver.solve()
```

---

## Installation Troubleshooting

### ImportError: No module named 'physrag'
```bash
# Make sure installation succeeded
pip install -e .

# Then verify again
python -c "import physrag; print(physrag.__file__)"
```

### ImportError: No module named 'tidalflow'
You're trying to use tidalflow integration without proper setup.

**Solution:** Install tidalflow (see [Using with tidalflow](#using-with-tidalflow) above)

```bash
# Check if you're in the right environment
conda activate tidalflow
python -c "import tidalflow; print('OK')"
```

### ModuleNotFoundError with integration
```bash
# Make sure you're in the conda environment
conda activate tidalflow

# Then try again
python your_script.py
```

### tidalflow installation fails
Check that all conda dependencies are available:
```bash
cd TidalFlow-SWE
conda env create -f environment.yml
conda activate tidalflow
```

---

## Next Steps

- **API Details:** See [API Reference](./api.md)
- **Design & Architecture:** See [Architecture Guide](./architecture.md)
- **Usage Patterns:** See [Usage Guides](./guides.md)
- **All Modules:** See [Module Reference](../physrag/index.md)
