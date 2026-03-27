# API Reference

Complete API documentation for PhysRAG-SWE modules and classes.

## physrag.config

Configuration management for SWE simulations.

### Classes

#### `SimulationConfig`

Dataclass for complete simulation configuration.

**Attributes:**
- `lon_range` (tuple) — Longitude range as (west, east)
- `lat_range` (tuple) — Latitude range as (south, north)
- `nx` (int) — Number of grid points in x-direction (longitude)
- `ny` (int) — Number of grid points in y-direction (latitude)
- `t_start` (float, default 0.0) — Start time in seconds
- `t_end` (float) — End time in seconds
- `dx` (float, optional) — Grid spacing in meters (computed if not provided)
- `dy` (float, optional) — Grid spacing in meters (computed if not provided)
- `cfl` (float, default 0.9) — Courant-Friedrichs-Lewy number for stability
- `num_output_times` (int, default 10) — Number of output snapshots
- `coordinate_system` (str, default 'geographic') — 'geographic' or 'metric'
- `use_mpi` (bool, default False) — Enable MPI parallelization
- `num_processors` (int, default 1) — Number of MPI processes
- `boundary_conditions` (list, default [0, 0, 0, 0]) — [west, east, south, north] (0=wall, 1=open, 2=periodic)

**Methods:**

##### `validate()`
Validate configuration parameters. Raises `ConfigurationError` if invalid.

**Example:**
```python
from physrag.config import SimulationConfig

config = SimulationConfig(
    lon_range=(-80.1865, -80.0791),
    lat_range=(25.6678, 25.9137),
    nx=40,
    ny=40,
    t_end=3600,  # 1 hour simulation
    cfl=0.9,
    boundary_conditions=[0, 1, 0, 1]  # walls on west/south, open on east/north
)
config.validate()
```

---

## physrag.solver

Main SWE solver and integration module.

### Classes

#### `SWESolver`

Core solver for 2D Shallow Water Equations using PyClaw.

**Constructor:**
```python
SWESolver(config: SimulationConfig)
```

**Parameters:**
- `config` — SimulationConfig instance

**Methods:**

##### `set_bathymetry(bathymetry, coordinate_type='geographic')`
Set bathymetry field for simulation.

**Parameters:**
- `bathymetry` (numpy.ndarray) — 2D bathymetry array (shape: ny×nx)
- `coordinate_type` (str) — 'geographic' or 'metric'

**Raises:**
- `ValueError` — Invalid array shape or coordinate type

**Example:**
```python
import numpy as np
solver = physrag.solver.SWESolver(config)

# Load bathymetry
bathy = np.load('bathymetry.npy')
solver.set_bathymetry(bathy, coordinate_type='geographic')
```

---

##### `set_initial_condition(water_surface, velocity_x=None, velocity_y=None)`
Set initial water surface elevation and optional velocities.

**Parameters:**
- `water_surface` (numpy.ndarray) — 2D water surface elevation (m, shape: ny×nx)
- `velocity_x` (numpy.ndarray, optional) — 2D x-velocity (m/s)
- `velocity_y` (numpy.ndarray, optional) — 2D y-velocity (m/s)

**Example:**
```python
# Start with Gaussian bump
h = np.exp(-((x - x0)**2 + (y - y0)**2) / sigma**2)
solver.set_initial_condition(h)
```

---

##### `set_wind_forcing(wind_x, wind_y, ramp_time=300)`
Set wind stress forcing (hurricane or constant wind).

**Parameters:**
- `wind_x` (float or callable) — Zonal wind stress (Pa) or function(t) → float
- `wind_y` (float or callable) — Meridional wind stress (Pa) or function(t) → float
- `ramp_time` (float) — Time to ramp up wind (seconds)

**Example:**
```python
# Hurricane wind stress
def wind_x(t):
    if t < 300:
        return t / 300 * 100  # Ramp up to 100 Pa
    else:
        return 100  # Constant stress

solver.set_wind_forcing(wind_x=wind_x, wind_y=0, ramp_time=300)
```

---

##### `setup_solver()`
Initialize and validate solver setup. Must be called before `solve()`.

**Raises:**
- `ConfigurationError` — Missing required setup (bathymetry, etc.)

---

##### `solve()`
Execute SWE simulation.

**Returns:**
- `SWEResult` — Solution container with output times and state variables

**Example:**
```python
solutions = solver.solve()
print(f"Solution shape: {solutions.h.shape}")  # (num_times, ny, nx)
```

---

#### `CoordinateMapper`

Transform coordinates between geographic (lon/lat) and metric (x/y) spaces.

**Constructor:**
```python
CoordinateMapper(config: SimulationConfig)
```

**Methods:**

##### `geographic_to_metric(lon, lat)`
Convert geographic to metric coordinates.

**Parameters:**
- `lon` (float or numpy.ndarray) — Longitude
- `lat` (float or numpy.ndarray) — Latitude

**Returns:**
- `tuple` — (x, y) in meters

---

##### `metric_to_geographic(x, y)`
Convert metric to geographic coordinates.

**Parameters:**
- `x` (float or numpy.ndarray) — X-coordinate (meters)
- `y` (float or numpy.ndarray) — Y-coordinate (meters)

**Returns:**
- `tuple` — (lon, lat)

---

## physrag.bathymetry_retrieval

Bathymetry data acquisition from GEBCO and custom sources.

### Functions

#### `download_gebco_ascii(extent, keep_csv=False, keep_txt=False)`

Download GEBCO bathymetry data via OPeNDAP.

**Parameters:**
- `extent` (tuple) — Bounding box (west, east, south, north)
- `keep_csv` (bool) — Save as CSV
- `keep_txt` (bool) — Keep temporary ASCII file

**Returns:**
- `pandas.DataFrame` — Columns: longitude, latitude, elevation (meters)

**Raises:**
- `ConnectionError` — OPeNDAP server unavailable
- `ValueError` — Invalid extent

---

#### `get_gebco_data(extent, keep_csv=False, keep_txt=False)`

Download GEBCO and return DataFrame with file paths.

**Returns:**
- `tuple` — (DataFrame, csv_path, txt_path)

---

### Classes

#### `BathymetryProvider`

Abstract base class for bathymetry sources.

**Methods:**

##### `get_bathymetry(extent, resolution=None)`
Retrieve bathymetry for geographic extent.

**Parameters:**
- `extent` (tuple) — Bounding box (west, east, south, north)
- `resolution` (float, optional) — Grid spacing in degrees

**Returns:**
- `numpy.ndarray` — 2D bathymetry array

---

#### `GEBCOBathymetryProvider`

Built-in provider for GEBCO bathymetry retrieval.

**Constructor:**
```python
GEBCOBathymetryProvider(cache_dir='./gebco_data')
```

**Methods:**

##### `get_bathymetry(extent, resolution=None, method='nearest')`
Retrieve GEBCO bathymetry for extent.

**Parameters:**
- `extent` (tuple) — Bounding box (west, east, south, north)
- `resolution` (float, optional) — Grid spacing in degrees
- `method` (str) — Interpolation method ('nearest', 'linear', 'cubic')

**Returns:**
- `numpy.ndarray` — 2D bathymetry array on regular grid

---

## physrag.data_interpolation

Module for interpolating sparse 2D point measurements.

### Classes

#### `SparseDataInterpolator`

Interpolator for sparse 2D data with multiple methods.

**Constructor:**
```python
SparseDataInterpolator(x, y, values, method='rbf')
```

**Parameters:**
- `x` (array-like) — X coordinates (longitude)
- `y` (array-like) — Y coordinates (latitude)
- `values` (array-like) — Data values at (x, y) points
- `method` (str) — Interpolation method ('rbf', 'kriging', 'idw', 'linear')

**Methods:**

##### `interpolate(x_new, y_new, return_uncertainty=True)`

Interpolate values at new points.

**Parameters:**
- `x_new` (array-like or ndarray) — New X coordinates
- `y_new` (array-like or ndarray) — New Y coordinates
- `return_uncertainty` (bool) — Return estimated uncertainties

**Returns:**
- `tuple` or `ndarray` — If return_uncertainty=True: (values, uncertainty), else just values

**Example:**
```python
import numpy as np
import physrag

# Station data: water level measurements
stations_lon = np.array([-87.2, -87.1, -87.15])
stations_lat = np.array([30.3, 30.35, 30.25])
measurements = np.array([1.2, 0.8, 1.0])  # Water level in meters

# Create interpolator
interp = physrag.data_interpolation.SparseDataInterpolator(
    x=stations_lon,
    y=stations_lat,
    values=measurements,
    method='rbf'
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
```

---

## physrag.result

Solution output and analysis module.

### Classes

#### `SWEResult`

Container for SWE simulation results.

**Attributes:**
- `h` (ndarray) — Water surface elevation at each time step (shape: num_times × ny × nx)
- `u` (ndarray) — X-velocity component
- `v` (ndarray) — Y-velocity component
- `time` (ndarray) — Output times (seconds)
- `coord_meshgrid` (tuple) — (lon_mg, lat_mg) meshgrids
- `bathymetry` (ndarray) — Bathymetry array (ny × nx)
- `config` (SimulationConfig) — Original simulation configuration

**Methods:**

##### `get_time_series(i, j, variable='h')`
Extract time series at grid point (i, j).

**Parameters:**
- `i`, `j` (int) — Grid indices
- `variable` (str) — 'h' (elevation), 'u' (x-velocity), 'v' (y-velocity)

**Returns:**
- `ndarray` — Time series array

---

##### `max_elevation()`
Compute maximum water elevation over time at each grid point.

**Returns:**
- `ndarray` — Max elevation field (ny × nx)

---

##### `inundation_depth()`
Compute inundation depth (water surface - bathymetry).

**Returns:**
- `ndarray` — Inundation at final time (ny × nx)

---

##### `export_netcdf(filename)`
Export solution to NetCDF format.

**Parameters:**
- `filename` (str) — Output file path

---

## physrag.providers

Data provider base classes and protocols.

### Classes

#### `DataProvider`

Abstract base class for all data providers.

**Methods:**

##### `get_data(extent, **kwargs)`
Retrieve data for geographic extent.

**Returns:**
- Depends on provider type

---

#### `InitialConditionProvider`

Provider for initial water surface elevation.

**Methods:**

##### `get_initial_condition(extent, resolution)`
Get initial water surface elevation.

**Returns:**
- `ndarray` — 2D initial elevation field

---

#### `WindProvider`

Provider for wind forcing parameters.

**Methods:**

##### `get_wind_stress(time, extent)`
Get wind stress components at time.

**Parameters:**
- `time` (float) — Time in seconds
- `extent` (tuple) — Geographic extent

**Returns:**
- `tuple` — (wind_x_stress_Pa, wind_y_stress_Pa)

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
