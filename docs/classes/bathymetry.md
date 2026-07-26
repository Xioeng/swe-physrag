# Bathymetry Retrieval & Interpolation

Guide to retrieving, loading, and interpolating bathymetry data in PhysRAG-SWE.

## Overview

Bathymetry is the foundation of realistic coastal simulations. PhysRAG-SWE provides multiple ways to access bathymetry data:
- **GEBCO 2025**: Global elevation model via OPeNDAP or local NetCDF
- **Local Data**: Existing NetCDF, CSV, or numpy arrays
- **Custom Sources**: User-defined bathymetry functions

---

## GEBCO Data Retrieval

### Automatic Download via OPeNDAP

Retrieve GEBCO data directly from remote servers without manual download:

```python
import physrag
from physrag.bathymetry_retrieval import download_gebco_ascii

# Download for a coastal region
extent = (-80.1865, -80.0791, 25.6678, 25.9137)  # Miami area
bathymetry_df = download_gebco_ascii(
    extent=extent
)

print(f"Downloaded {len(bathymetry_df)} bathymetry points")
print(bathymetry_df.head())
```

**Parameters:**
- `extent`: (lon_min, lon_max, lat_min, lat_max) tuple
- `output_path`: Optional path to save CSV
- `resolution`: Grid resolution in degrees (default: 0.001°)
- `timeout`: Request timeout in seconds (default: 60)

**Returns:**
- `DataFrame` with columns: longitude, latitude, elevation

### Local NetCDF Files

Load GEBCO data from local NetCDF files (fastest for repeated use):

```python
import physrag
from physrag.bathymetry_retrieval import load_gebco_netcdf

# Load local NetCDF file
bathymetry = load_gebco_netcdf(
    nc_path="data/gebco_2025_miami.nc",
    lon_range=(-80.2, -80.0),
    lat_range=(25.6, 25.95)
)

print(f"Loaded bathymetry shape: {bathymetry.shape}")
print(f"Depth range: {bathymetry.min():.1f} to {bathymetry.max():.1f} m")
```

**Where to get files:**
1. Visit https://www.gebco.net/data_and_products/gridded_bathymetry_data/
2. Select your region
3. Download **NetCDF format** (not ASCII or GeoTIFF)
4. Save to `data/` directory

---

## Interpolation

### Grid Interpolation

Interpolate bathymetry data to simulation grid coordinates:

```python
import physrag
import numpy as np

# Create simulation grid
config = physrag.config.SimulationConfig(
    lon_range=(-80.1865, -80.0791),
    lat_range=(25.6678, 25.9137),
    nx=40,
    ny=40,
    # ... other parameters
)

solver = physrag.solver.SWESolver(config=config)

# Get grid coordinates
X_coord = solver.X_coord  # (ny, nx) in degrees
Y_coord = solver.Y_coord  # (ny, nx) in degrees

# Interpolate GEBCO to grid
bathymetry = physrag.utils.interpolate_gebco_on_grid(
    X=X_coord,
    Y=Y_coord,
    nc_path="data/gebco_2025_miami.nc",
    method='linear'
)

# Handle NaN values (land/missing data)
bathymetry[np.isnan(bathymetry)] = 0.0

# Set in solver
solver.set_bathymetry(bathymetry)
```

### RBF Interpolation

For scattered data points (tide gauges, surveys):

```python
import physrag
import numpy as np
import pandas as pd

# Load survey data
survey = pd.read_csv("data/bathymetry_survey.csv")
x_survey = survey['longitude'].values
y_survey = survey['latitude'].values
z_survey = survey['depth'].values  # Negative values for depth below MSL

# Create interpolator
interpolator = physrag.data_interpolation.SparseDataInterpolator(
    x=x_survey,
    y=y_survey,
    values=z_survey,
    method='rbf',
    rbf_function='thin_plate',
    epsilon=1.0  # RBF parameter
)

# Interpolate to grid
bathymetry, uncertainty = interpolator.interpolate(
    X_coord.flatten(),
    Y_coord.flatten()
)

bathymetry = bathymetry.reshape(X_coord.shape)
uncertainty = uncertainty.reshape(X_coord.shape)

print(f"Interpolation uncertainty range: {uncertainty.min():.3f} to {uncertainty.max():.3f} m")
```

**RBF Functions:**
- `'thin_plate'`: Smooth, recommended for bathymetry
- `'multiquadric'`: Less smooth, faster
- `'inverse_multiquadric'`: Alternative smooth option
- `'gaussian'`: Radial gaussian function

### Kriging Interpolation

For data with spatial correlation structure:

```python
import physrag

# Create kriging interpolator
interpolator = physrag.data_interpolation.SparseDataInterpolator(
    x=x_survey,
    y=y_survey,
    values=z_survey,
    method='kriging',
    variogram_model='exponential',  # or 'spherical', 'gaussian'
    nlags=6
)

bathymetry, variance = interpolator.interpolate(
    X_coord.flatten(),
    Y_coord.flatten()
)

# Use variance as uncertainty estimate
std_uncertainty = np.sqrt(variance).reshape(X_coord.shape)
```

---

## Bathymetry Providers

### GEBCOBathymetryProvider

```python
from physrag.bathymetry_retrieval import GEBCOBathymetryProvider

# Create provider
provider = GEBCOBathymetryProvider(
    nc_path="data/gebco_2025_miami.nc",
    method='linear'
)

# Use with solver
bathymetry = provider(solver.X_coord, solver.Y_coord)
solver.set_bathymetry(bathymetry)
```

### Custom Bathymetry Provider

```python
import numpy as np
from physrag.bathymetry_retrieval import BathymetryProvider

class AnalyticBathymetryProvider(BathymetryProvider):
    """Analytic shelf-slope bathymetry model."""
    
    def __call__(self, x, y):
        """
        Parametric bathymetry model.
        
        Parameters
        ----------
        x : ndarray
            Longitude (degrees)
        y : ndarray
            Latitude (degrees)
            
        Returns
        -------
        ndarray
            Bathymetry (m). Negative = depth, positive = elevation
        """
        # Linear shelf: deepens from west to east
        shelf_depth = -1000 * (x + 80.2) / 0.2
        
        # Gaussian shelf break feature
        feature = -500 * np.exp(-((y - 25.7)**2) / 0.05)
        
        return np.minimum(shelf_depth + feature, 0)  # Ensure negative (depths)

# Use in simulation
provider = AnalyticBathymetryProvider()
bathymetry = provider(solver.X_coord, solver.Y_coord)
```

---

## Data Processing

### Validate Bathymetry

```python
import numpy as np
import matplotlib.pyplot as plt

# Check statistics
print(f"Min depth: {bathymetry.min():.1f} m")
print(f"Max elevation: {bathymetry.max():.1f} m")
print(f"Mean depth: {bathymetry[bathymetry < 0].mean():.1f} m")
print(f"Num land points: {(bathymetry > 0).sum()}")
print(f"Num NaN: {np.isnan(bathymetry).sum()}")

# Visual inspection
plt.figure(figsize=(12, 8))
plt.contourf(solver.X_coord, solver.Y_coord, bathymetry, levels=20, cmap='ocean_r')
plt.colorbar(label='Elevation (m)')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Bathymetry')
plt.show()
```

### Smooth Bathymetry

```python
from scipy.ndimage import gaussian_filter

# Smooth sharp features (reduces noise/artifacts)
bathymetry_smooth = gaussian_filter(bathymetry, sigma=1.0)

# Verify smoothing
plt.figure(figsize=(12, 5))
plt.subplot(121)
plt.contourf(solver.X_coord, solver.Y_coord, bathymetry, levels=20, cmap='ocean_r')
plt.title('Original')
plt.subplot(122)
plt.contourf(solver.X_coord, solver.Y_coord, bathymetry_smooth, levels=20, cmap='ocean_r')
plt.title('Smoothed')
plt.show()
```

### Handle Missing Data

```python
import numpy as np
from scipy.interpolate import griddata

# Separate water and land
is_water = bathymetry < 0
is_land = bathymetry >= 0
is_nan = np.isnan(bathymetry)

# Interpolate missing values
if is_nan.any():
    points = np.where(~is_nan)
    values = bathymetry[~is_nan]
    
    bathymetry[is_nan] = griddata(
        (solver.X_coord[points], solver.Y_coord[points]),
        values,
        (solver.X_coord[is_nan], solver.Y_coord[is_nan]),
        method='linear'
    )

# Ensure reasonable depth range
bathymetry[bathymetry < -5000] = -5000  # Cap max depth
bathymetry[bathymetry > 500] = 500      # Cap max land elevation
```

---

## Performance Tips

### 1. Cache Data

```python
import os
from pathlib import Path

cache_dir = "data/gebco_cache"
cache_file = f"{cache_dir}/bathymetry_40x40.npy"

if os.path.exists(cache_file):
    # Load from cache
    bathymetry = np.load(cache_file)
else:
    # Compute and cache
    bathymetry = interpolate_gebco_on_grid(...)
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    np.save(cache_file, bathymetry)
```

### 2. Use Efficient Interpolation

```python
# For quick testing: nearest neighbor
bathymetry = interpolate_gebco_on_grid(..., method='nearest')

# For production: linear
bathymetry = interpolate_gebco_on_grid(..., method='linear')

# For high accuracy: cubic (slower)
bathymetry = interpolate_gebco_on_grid(..., method='cubic')
```

### 3. Parallel Processing

```python
import functools
from multiprocessing import Pool

# Define interpolation as partially applied function
interp_func = functools.partial(
    interpolate_gebco_on_grid,
    nc_path="data/gebco_2025.nc"
)

# Process multiple grids in parallel
grids = [grid1, grid2, grid3, grid4]
with Pool(4) as pool:
    bathymetries = pool.map(interp_func, grids)
```

---

## References

- **GEBCO Dataset**: https://www.gebco.net/
- **GEBCO 2025 Documentation**: https://www.gebco.net/data_and_products/gridded_bathymetry_data/gebco_2025/
- **OPeNDAP Protocol**: https://www.opendap.org/
- **RBF Interpolation**: Wendland, H. (2005). *Scattered Data Approximation*
- **Kriging**: Cressie, N. (1993). *Statistics for Spatial Data*

---
