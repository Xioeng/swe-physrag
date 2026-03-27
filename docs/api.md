# API Reference

Complete API documentation for physrag modules.

## physrag.bathymetry_retrieval

Module for downloading and processing GEBCO bathymetry data via OPeNDAP.

### Functions

#### `download_gebco_ascii(extent, keep_csv=False, keep_txt=False)`

Download GEBCO bathymetry data for a geographic extent.

**Parameters:**
- `extent` (tuple) — Bounding box as (west, east, south, north) in lon/lat coordinates
- `keep_csv` (bool, default False) — Save data as CSV file
- `keep_txt` (bool, default False) — Keep temporary ASCII file

**Returns:**
- `pandas.DataFrame` — GEBCO data with columns: Longitude, Latitude, Elevation

**Raises:**
- `ValueError` — Invalid extent format
- `ConnectionError` — Failed to connect to OPeNDAP server

**Example:**
```python
df = physrag.bathymetry_retrieval.download_gebco_ascii(
    extent=(-87.23, -87.09, 30.20, 30.40),
    keep_csv=True
)
print(df[['Longitude', 'Latitude', 'Elevation']].head())
```

---

#### `get_gebco_data(extent, keep_csv=False, keep_txt=False)`

Download GEBCO data and return paths (DataFrame, CSV path, TXT path).

**Parameters:**
- `extent` (tuple) — Bounding box (west, east, south, north)
- `keep_csv` (bool) — Save CSV file
- `keep_txt` (bool) — Keep temporary ASCII file

**Returns:**
- `tuple` — (DataFrame, csv_path, txt_path)

**Example:**
```python
df, csv_path, txt_path = physrag.bathymetry_retrieval.get_gebco_data(
    extent=(-87.23, -87.09, 30.20, 30.40),
    keep_csv=True
)
print(f"CSV saved to: {csv_path}")
```

---

## physrag.rag_data_retrieval

Module for filtering and processing CSV data by geographic extent.

### Functions

#### `read_csv_extent(csv_path, extent, lat_col, lon_col, columns=None, timestamp_col=None, start_time=None, end_time=None)`

Load CSV file and filter by geographic extent and optional time range.

**Parameters:**
- `csv_path` (str) — Path to CSV file
- `extent` (tuple) — Bounding box (west, east, south, north)
- `lat_col` (str) — Column name for latitude
- `lon_col` (str) — Column name for longitude
- `columns` (list, optional) — Specific columns to load (None loads all)
- `timestamp_col` (str, optional) — Column name for timestamps
- `start_time` (str, optional) — ISO 8601 start time (e.g., "2024-02-01T00:00:00Z")
- `end_time` (str, optional) — ISO 8601 end time

**Returns:**
- `pandas.DataFrame` — Filtered data

**Example:**
```python
df = physrag.rag_data_retrieval.read_csv_extent(
    csv_path="weather.csv",
    extent=(-87.23, -87.09, 30.20, 30.40),
    lat_col="latitude_decimal_degrees",
    lon_col="longitude_decimal_degrees",
    columns=["station_name", "water_level_m_mllw", "temperature_c"],
    timestamp_col="timestamp_utc_iso8601",
    start_time="2024-02-01T00:00:00Z",
    end_time="2024-02-02T00:00:00Z"
)
```

---

#### `filter_by_extent(df, extent, lat_col, lon_col)`

Filter existing DataFrame by geographic extent.

**Parameters:**
- `df` (pandas.DataFrame) — Input DataFrame
- `extent` (tuple) — Bounding box (west, east, south, north)
- `lat_col` (str) — Latitude column name
- `lon_col` (str) — Longitude column name

**Returns:**
- `pandas.DataFrame` — Filtered DataFrame

---

#### `load_csv(csv_path, columns=None, timestamp_col=None, start_time=None, end_time=None)`

Load CSV file with optional column and temporal filtering.

**Parameters:**
- `csv_path` (str) — Path to CSV file
- `columns` (list, optional) — Columns to load
- `timestamp_col` (str, optional) — Column with timestamps
- `start_time` (str, optional) — ISO 8601 start time
- `end_time` (str, optional) — ISO 8601 end time

**Returns:**
- `pandas.DataFrame` — Loaded data

---

## physrag.data_interpolation

Module for interpolating sparse 2D point measurements.

### Classes

#### `SparseDataInterpolator`

Interpolator for 2D sparse data using RBF (Radial Basis Function).

**Constructor:**
```python
SparseDataInterpolator(x, y, values)
```

**Parameters:**
- `x` (array-like) — X coordinates (longitude)
- `y` (array-like) — Y coordinates (latitude)
- `values` (array-like) — Data values at (x, y) points

**Methods:**

##### `interpolate(x_new, y_new)`

Interpolate values at new points.

**Parameters:**
- `x_new` (array-like) — New X coordinates
- `y_new` (array-like) — New Y coordinates

**Returns:**
- `tuple` — (interpolated_values, uncertainties)
  - `interpolated_values` (ndarray) — Interpolated values
  - `uncertainties` (ndarray) — Estimated uncertainties

**Example:**
```python
import numpy as np
import physrag

# Create interpolator from measurements
interp = physrag.data_interpolation.SparseDataInterpolator(
    x=np.array([-87.2, -87.1, -87.15]),
    y=np.array([30.3, 30.35, 30.25]),
    values=np.array([1.2, 0.8, 1.0])
)

# Interpolate on regular grid
lon_grid = np.linspace(-87.25, -87.05, 50)
lat_grid = np.linspace(30.2, 30.4, 50)
lon_mg, lat_mg = np.meshgrid(lon_grid, lat_grid)

interp_values, uncertainties = interp.interpolate(
    lon_mg.flatten(),
    lat_mg.flatten()
)

# Reshape to grid
interp_grid = interp_values.reshape(lon_mg.shape)
uncert_grid = uncertainties.reshape(lon_mg.shape)
```

---

## physrag.integrations.tidalflow_providers

Optional integration module for adapting physrag data to tidalflow.

**Requires:** tidalflow installed (conda environment setup)

### Classes

#### `BathymetryFromGEBCO`

Bathymetry provider using GEBCO data for tidalflow.

**Constructor:**
```python
BathymetryFromGEBCO(extent, keep_csv=False, csv_path=None)
```

**Parameters:**
- `extent` (tuple) — Bounding box (west, east, south, north)
- `keep_csv` (bool) — Save downloaded data as CSV
- `csv_path` (str, optional) — Path to pre-downloaded CSV file

**Methods:**

##### `get_bathymetry(lon_grid, lat_grid)`

Get bathymetry values at grid points.

**Parameters:**
- `lon_grid` (ndarray) — 2D longitude grid
- `lat_grid` (ndarray) — 2D latitude grid

**Returns:**
- `ndarray` — Bathymetry elevation at grid points

**Example:**
```python
from physrag.integrations.tidalflow_providers import BathymetryFromGEBCO
import numpy as np

provider = BathymetryFromGEBCO(
    extent=(-87.23, -87.09, 30.20, 30.40),
    keep_csv=True
)

# Create grid
lon_grid = np.linspace(-87.23, -87.09, 50)
lat_grid = np.linspace(30.20, 30.40, 50)
lon_mg, lat_mg = np.meshgrid(lon_grid, lat_grid)

# Get bathymetry
bathymetry = provider.get_bathymetry(lon_mg, lat_mg)
```

---

#### `WaterLevelInterpolationProvider`

Water level provider using interpolated sparse measurements.

**Constructor:**
```python
WaterLevelInterpolationProvider(lon, lat, values)
```

**Parameters:**
- `lon` (array-like) — Measurement longitudes
- `lat` (array-like) — Measurement latitudes
- `values` (array-like) — Water level values

**Methods:**

##### `get_initial_condition(lon_grid, lat_grid)`

Get initial water depth at grid points for tidalflow.

**Parameters:**
- `lon_grid` (ndarray) — 2D longitude grid
- `lat_grid` (ndarray) — 2D latitude grid

**Returns:**
- `ndarray` — Shape (3, nx, ny) with [water_depth, x_momentum, y_momentum]

**Example:**
```python
from physrag.integrations.tidalflow_providers import WaterLevelInterpolationProvider
import numpy as np

# Measurement data
lons = np.array([-87.2, -87.1, -87.15])
lats = np.array([30.3, 30.35, 30.25])
levels = np.array([1.2, 0.8, 1.0])

provider = WaterLevelInterpolationProvider(
    lon=lons,
    lat=lats,
    values=levels
)

# Create grid
lon_grid = np.linspace(-87.23, -87.09, 50)
lat_grid = np.linspace(30.20, 30.40, 50)
lon_mg, lat_mg = np.meshgrid(lon_grid, lat_grid)

# Get initial condition (3, ny, nx)
ic = provider.get_initial_condition(lon_mg, lat_mg)
print(ic.shape)  # (3, 50, 50)
```

---

## Module Organization

```
physrag/
├── bathymetry_retrieval/
│   ├── __init__.py
│   ├── query.py          → build_query()
│   ├── retrieval.py      → download_gebco_ascii()
│   └── conversion.py     → parse_gebco_ascii()
│
├── rag_data_retrieval/
│   ├── __init__.py
│   └── csv_retrieval.py  → read_csv_extent(), filter_by_extent()
│
├── data_interpolation/
│   ├── __init__.py
│   └── sparse_interpolator.py → SparseDataInterpolator
│
├── integrations/
│   ├── __init__.py
│   └── tidalflow_providers.py
│       ├── BathymetryFromGEBCO
│       └── WaterLevelInterpolationProvider
│
└── __init__.py
```

---

## Error Handling

### Common Exceptions

| Error | Cause | Solution |
|-------|-------|----------|
| `ImportError: No module named 'tidalflow'` | tidalflow not installed | Install tidalflow in conda environment |
| `ValueError: Invalid extent` | Bad extent format | Use (west, east, south, north) |
| `ConnectionError` | OPeNDAP server unreachable | Check internet connection; GEBCO servers may be down |
| `FileNotFoundError` | CSV file not found | Check csv_path parameter |
| `KeyError` | Column name not found | Check lat_col/lon_col parameters match actual CSV columns |
