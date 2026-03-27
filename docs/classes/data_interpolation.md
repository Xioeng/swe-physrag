# Data Interpolation

Comprehensive guide to sparse data interpolation in PhysRAG-SWE.

## Overview

Data interpolation enables PhysRAG-SWE to integrate observational data (tide gauges, buoys, surveys) with physics-based simulations. Multiple interpolation methods are available with uncertainty quantification.

---

## SparseDataInterpolator

Main interpolation class for scattered point data:

```python
from physrag.data_interpolation import SparseDataInterpolator
import numpy as np

# Create interpolator from observations
interpolator = SparseDataInterpolator(
    x=observation_x,              # 1D array of observation locations (x/lon)
    y=observation_y,              # 1D array of observation locations (y/lat)
    values=observation_values,    # 1D array of measured values
    method='rbf',                 # Interpolation method
    rbf_function='thin_plate',    # RBF kernel function
    epsilon=None,                 # RBF shape parameter (auto-computed)
    smooth=0.0,                   # Smoothing parameter
)

# Interpolate to regular grid
x_grid, y_grid = np.meshgrid(
    np.linspace(-80.2, -80.0, 100),
    np.linspace(25.6, 25.95, 100)
)

gridded_values, uncertainty = interpolator.interpolate(
    x_grid.flatten(),
    y_grid.flatten()
)

gridded_values = gridded_values.reshape(x_grid.shape)
uncertainty = uncertainty.reshape(x_grid.shape)
```

## Interpolation Methods

### RBF (Radial Basis Function)

Smooth interpolation using radial basis functions:

```python
interpolator = SparseDataInterpolator(
    x=x_obs, y=y_obs, values=z_obs,
    method='rbf',
    rbf_function='thin_plate',    # Recommended for bathymetry
    epsilon=1.0,                   # Shape parameter
    smooth=1e-6                    # Regularization
)
```

**RBF Functions:**

| Function | Formula | Use Case |
|----------|---------|----------|
| `'thin_plate'` | $r^2 \ln(r)$ | Smooth bathymetry, general use |
| `'multiquadric'` | $\sqrt{1 + (\epsilon r)^2}$ | Some oscillation, faster |
| `'inverse_multiquadric'` | $1/\sqrt{1 + (\epsilon r)^2}$ | Smooth, localized |
| `'gaussian'` | $\exp(-(\epsilon r)^2)$ | Smooth, fast decay |

**Parameters:**

- `epsilon`: Shape parameter (default: auto-computed from data spacing)
  - Larger: more localized
  - Smaller: more global
- `smooth`: Regularization parameter (default: 0.0)
  - 0: Exact interpolation
  - >0: Smoothing, handles noisy data

**Example with Regularization:**

```python
# Noisy water level data
interpolator = SparseDataInterpolator(
    x=x_gauges, y=y_gauges, values=water_level,
    method='rbf',
    rbf_function='thin_plate',
    smooth=0.01  # Some smoothing for noisy data
)
```

### Kriging

Geostatistical interpolation with spatial correlation:

```python
interpolator = SparseDataInterpolator(
    x=x_obs, y=y_obs, values=z_obs,
    method='kriging',
    variogram_model='exponential',  # 'exponential', 'spherical', 'gaussian'
    nlags=6,                         # Number of lags for variogram
    weight=True,                     # Distance-weighted kriging
)

# Interpolate
gridded_values, variance = interpolator.interpolate(x_grid, y_grid)
std_dev = np.sqrt(variance)
```

**Variogram Models:**

- `'exponential'`: Recommended for most applications
- `'spherical'`: Bounded spatial correlation
- `'gaussian'`: Smooth spatial correlation
- `'power'`: Power law behavior

**Parameters:**

- `nlags`: Number of lag bins for variogram estimation (6-12 typical)
- `weight`: Distance-weighting for semivariance estimation
- `verbose`: Print variogram fitting details

### Inverse Distance Weighting (IDW)

Fast interpolation with distance weighting:

```python
interpolator = SparseDataInterpolator(
    x=x_obs, y=y_obs, values=z_obs,
    method='idw',
    power=2.0,              # Power parameter (higher = more local)
    threshold_dist=None,    # Max distance to include point
)
```

**Parameters:**

- `power`: Weighting exponent (default: 2.0)
  - 1: Linear distance weighting
  - 2: Inverse distance squared
  - Higher: More weight to closest points
- `threshold_dist`: Maximum distance to include points in interpolation

### Linear Interpolation

Simple triangulation-based interpolation:

```python
interpolator = SparseDataInterpolator(
    x=x_obs, y=y_obs, values=z_obs,
    method='linear',
    fill_value=np.nan  # Value outside convex hull
)
```

**Limitations:**
- Only interpolates (no extrapolation)
- Can be slow for large datasets
- May produce artifacts at domain boundaries

---

## Uncertainty Quantification

### RBF Uncertainty

RBF methods provide practical uncertainty estimates:

```python
interpolator = SparseDataInterpolator(
    x=x_obs, y=y_obs, values=z_obs,
    method='rbf',
    rbf_function='thin_plate'
)

values, uncertainty = interpolator.interpolate(x_grid, y_grid)

# Visualize uncertainty
plt.figure(figsize=(12, 4))

plt.subplot(121)
plt.contourf(x_grid, y_grid, values, levels=20)
plt.colorbar(label='Value')
plt.title('Interpolated Values')

plt.subplot(122)
plt.contourf(x_grid, y_grid, uncertainty, levels=20, cmap='Reds')
plt.colorbar(label='Uncertainty')
plt.title('Uncertainty Estimate')

plt.show()
```

### Kriging Variance

Kriging provides theoretical variance estimates:

```python
interpolator = SparseDataInterpolator(
    x=x_obs, y=y_obs, values=z_obs,
    method='kriging'
)

values, variance = interpolator.interpolate(x_grid, y_grid)

# Confidence intervals
std = np.sqrt(variance)
ci_lower = values - 1.96 * std  # 95% CI
ci_upper = values + 1.96 * std

plt.fill_between(x_grid[0], ci_lower[0], ci_upper[0], alpha=0.3)
```

---

## Real-World Applications

### Water Level Interpolation

```python
import physrag
import pandas as pd

# Load tide gauge observations
gauges = pd.read_csv("data/noaa_tide_gauges.csv")
# Columns: station_id, longitude, latitude, water_level, timestamp

# Filter by time period
gauges = gauges[
    (gauges['timestamp'] >= '2023-09-01') &
    (gauges['timestamp'] <= '2023-09-30')
]

# Create interpolator
interpolator = SparseDataInterpolator(
    x=gauges['longitude'].values,
    y=gauges['latitude'].values,
    values=gauges['water_level'].values,
    method='rbf',
    rbf_function='thin_plate',
    smooth=0.005  # Smooth noisy gauge data
)

# Get initial condition for simulation
h_init, uncertainty = interpolator.interpolate(
    solver.X_coord.flatten(),
    solver.Y_coord.flatten()
)

h_init = h_init.reshape(solver.X_coord.shape)
uncertainty = uncertainty.reshape(solver.X_coord.shape)

print(f"Water level range: {h_init.min():.2f} to {h_init.max():.2f} m")
print(f"Uncertainty range: {uncertainty.min():.3f} to {uncertainty.max():.3f} m")
```

### Bathymetry Survey Integration

```python
import physrag
import pandas as pd

# Load multi-beam sonar survey
survey = pd.read_csv("data/multibeam_survey.csv")
# Columns: longitude, latitude, depth, uncertainty

# Create kriging interpolator for spatial correlation
interpolator = SparseDataInterpolator(
    x=survey['longitude'].values,
    y=survey['latitude'].values,
    values=survey['depth'].values,
    method='kriging',
    variogram_model='exponential',
    nlags=8
)

bathymetry, variance = interpolator.interpolate(
    solver.X_coord.flatten(),
    solver.Y_coord.flatten()
)

bathymetry = bathymetry.reshape(solver.X_coord.shape)

# Combine with GEBCO for areas without survey data
gebco = physrag.utils.interpolate_gebco_on_grid(...)
survey_coverage = ~np.isnan(bathymetry)
bathymetry[~survey_coverage] = gebco[~survey_coverage]
```

### Current Velocity Integration

```python
# Interpolate velocity components from observations
interpolator_u = SparseDataInterpolator(
    x=buoy_lon, y=buoy_lat,
    values=buoy_u_velocity,
    method='rbf'
)

interpolator_v = SparseDataInterpolator(
    x=buoy_lon, y=buoy_lat,
    values=buoy_v_velocity,
    method='rbf'
)

u_init, _ = interpolator_u.interpolate(x_grid, y_grid)
v_init, _ = interpolator_v.interpolate(x_grid, y_grid)

# Use as initial momentum (hu, hv) in simulation
initial_condition = np.stack([
    h_init,
    h_init * u_init,  # hu = h * u
    h_init * v_init,  # hv = h * v
], axis=0)
```

---

## Advanced Topics

### Cross-Validation

Evaluate interpolation error:

```python
from sklearn.model_selection import LeaveOneOut

# Cross-validation
loo = LeaveOneOut()
errors = []

for train_idx, test_idx in loo.split(x_obs):
    x_train, x_test = x_obs[train_idx], x_obs[test_idx]
    y_train, y_test = y_obs[train_idx], y_obs[test_idx]
    z_train, z_test = z_obs[train_idx], z_obs[test_idx]
    
    interp = SparseDataInterpolator(
        x=x_train, y=y_train, values=z_train,
        method='rbf'
    )
    
    z_pred, _ = interp.interpolate(x_test, y_test)
    error = np.abs(z_pred - z_test).item()
    errors.append(error)

print(f"Mean error: {np.mean(errors):.3f} m")
print(f"Std error: {np.std(errors):.3f} m")
```

### Adaptive Smoothing

Adjust smoothing parameter based on data noise:

```python
from scipy.stats import variation

# Estimate data noise from variability
cv = variation(z_obs)  # Coefficient of variation

if cv > 0.1:
    smooth = 0.05  # High noise: smooth aggressively
elif cv > 0.05:
    smooth = 0.01  # Moderate noise
else:
    smooth = 0.001  # Low noise: minimal smoothing

interpolator = SparseDataInterpolator(
    x=x_obs, y=y_obs, values=z_obs,
    method='rbf',
    smooth=smooth
)
```

### Extrapolation

Extrapolate beyond data bounds (with caution):

```python
from scipy.interpolate import Rbf

# Create RBF function directly for more control
rbf = Rbf(x_obs, y_obs, z_obs, function='thin_plate', epsilon=1.0)

# Evaluate anywhere (extrapolates if needed)
z_extrap = rbf(x_extrap, y_extrap)

# Mark extrapolated region
distances = np.minimum.reduce([
    np.abs(x_grid - x_obs.min()),
    np.abs(x_grid - x_obs.max()),
    np.abs(y_grid - y_obs.min()),
    np.abs(y_grid - y_obs.max())
])

is_extrapolated = distances > 0.1  # Beyond 0.1° from data
```

---

## Performance Optimization

### Subset Selection

Use stratified sampling for large datasets:

```python
from sklearn.cluster import KMeans

# Cluster observations
n_clusters = 50
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
clusters = kmeans.fit_predict(np.column_stack([x_obs, y_obs]))

# Select one representative point per cluster
x_selected, y_selected, z_selected = [], [], []
for cluster_id in range(n_clusters):
    mask = clusters == cluster_id
    idx = mask.nonzero()[0]
    idx_representative = idx[np.argmin(
        np.sqrt((x_obs[idx] - kmeans.cluster_centers_[cluster_id, 0])**2 +
                (y_obs[idx] - kmeans.cluster_centers_[cluster_id, 1])**2)
    )]
    x_selected.append(x_obs[idx_representative])
    y_selected.append(y_obs[idx_representative])
    z_selected.append(z_obs[idx_representative])

# Interpolate with reduced dataset
interpolator = SparseDataInterpolator(
    x=np.array(x_selected),
    y=np.array(y_selected),
    values=np.array(z_selected),
    method='rbf'
)
```

### Parallel Processing

Interpolate multiple grids in parallel:

```python
from multiprocessing import Pool
import functools

# Define partial function
interp_func = functools.partial(
    SparseDataInterpolator(x, y, z, method='rbf').interpolate
)

# Process multiple grids
x_grids = [grid1_x, grid2_x, grid3_x]
y_grids = [grid1_y, grid2_y, grid3_y]

with Pool(4) as pool:
    results = pool.starmap(interp_func, zip(x_grids, y_grids))
```

### Caching

Cache interpolators for reuse:

```python
import pickle

# Save interpolator
with open('tide_gauge_interpolator.pkl', 'wb') as f:
    pickle.dump(interpolator, f)

# Load later
with open('tide_gauge_interpolator.pkl', 'rb') as f:
    interpolator = pickle.load(f)

# Use for new grid
values, uncertainty = interpolator.interpolate(x_new, y_new)
```

---

## References

- **RBF Methods**: Wendland, H. (2005). *Scattered Data Approximation*
- **Kriging**: Cressie, N. (1993). *Statistics for Spatial Data*
- **Scipy Interpolation**: https://docs.scipy.org/doc/scipy/reference/interpolate.html
- **Scikit-learn Cross-validation**: https://scikit-learn.org/stable/modules/cross_validation.html

---
