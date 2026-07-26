# Usage Guides

Production workflows and best practices for PhysRAG-SWE simulations.

## Simple Shallow Water Simulation

### Minimal Example: Gaussian Wave

Start with a basic simulation without real data:

```python
import numpy as np
import physrag
from physrag.config import SimulationConfig
from physrag.solver import SWESolver

# Configure domain
config = SimulationConfig(
    lon_range=(-87.25, -87.05),
    lat_range=(30.2, 30.4),
    nx=50,
    ny=50,
    t_end=1800,  # 30 minutes
    num_output_times=10
)

# Create solver
solver = SWESolver(config=config)

# Set simple bathymetry (constant depth)
x, y = np.meshgrid(
    np.linspace(config.lon_range[0], config.lon_range[1], config.nx),
    np.linspace(config.lat_range[0], config.lat_range[1], config.ny)
)
bathymetry = -10 * np.ones_like(x)  # 10m constant depth
solver.set_bathymetry(bathymetry)

# Set Gaussian bump initial condition
h0 = 0.5 * np.exp(-((x + 87.15)**2 + (y - 30.3)**2) / 0.01**2)
solver.set_initial_condition(h0)

# Run simulation
solver.setup_solver()
solutions = solver.solve()

# Access results
print(f"Max elevation: {solutions.h.max():.3f} m")
print(f"Time steps: {len(solutions.time)}")
```

---

## GEBCO Bathymetry + Observations

### Complete Workflow: Real Bathymetry and Station Data

Integrate GEBCO bathymetry with water level observations:

```python
import numpy as np
import pandas as pd
import physrag
import tidalflow
from tidalflow.config import SimulationConfig
from tidalflow.solver import SWESolver
from physrag.bathymetry_retrieval import download_gebco_ascii
from physrag.data_interpolation import SparseDataInterpolator

extent = (-87.25, -87.05, 30.2, 30.4)

# 1. Download GEBCO bathymetry
print("Downloading GEBCO bathymetry...")
df_bathy = download_gebco_ascii(extent=extent, keep_csv=True)
print(f"GEBCO data shape: {df_bathy.shape}")

# Load into grid
x_unique = np.sort(df_bathy['Longitude'].unique())
y_unique = np.sort(df_bathy['Latitude'].unique())
x_mg, y_mg = np.meshgrid(x_unique, y_unique)

# Create interpolator
interp_bathy = SparseDataInterpolator(
    x=df_bathy['Longitude'].values,
    y=df_bathy['Latitude'].values,
    values=df_bathy['Elevation'].values,
    method='rbf'
)

bathymetry_grid, _ = interp_bathy.interpolate(x_mg.flatten(), y_mg.flatten())
bathymetry_grid = bathymetry_grid.reshape(x_mg.shape)

# 2. Load water level observations
obs_stations = pd.read_csv('data/water_level_stations.csv')  # lon, lat, water_level_m
print(f"Loaded {len(obs_stations)} stations")

# 3. Setup simulation
config = SimulationConfig(
    lon_range=extent[:2],
    lat_range=extent[2:],
    nx=len(x_unique),
    ny=len(y_unique),
    t_end=3600,
    num_output_times=20,
    boundary_conditions=[0, 1, 0, 1]  # walls W/S, open E/N
)

solver = SWESolver(config=config)
solver.set_bathymetry(bathymetry_grid)

# 4. Interpolate observations to initial condition
interp_obs = SparseDataInterpolator(
    x=obs_stations['longitude'].values,
    y=obs_stations['latitude'].values,
    values=obs_stations['water_level_m'].values,
    method='kriging'
)

h0, _ = interp_obs.interpolate(x_mg.flatten(), y_mg.flatten())
h0 = h0.reshape(x_mg.shape)
solver.set_initial_condition(h0)

# 5. Add wind (optional)
# Linear wind ramp followed by constant stress
def wind_stress(t):
    return 50 if t > 300 else t / 300 * 50

solver.set_wind_forcing(wind_x=wind_stress, wind_y=0)

# 6. Run simulation
solver.setup_solver()
solutions = solver.solve()

print(f"Simulation complete: {solutions.h.shape}")
print(f"Max inundation: {(solutions.h - bathymetry_grid).max():.2f} m")
```

---

## Hurricane Wind Forcing

### Time-Varying Wind from Observations

Simulate hurricane with realistic wind profile:

```python
import physrag
from physrag.config import SimulationConfig
from physrag.solver import SWESolver
import numpy as np

# Configuration
config = SimulationConfig(
    lon_range=(-87.5, -86.5),
    lat_range=(29.5, 30.5),
    nx=80,
    ny=80,
    t_end=86400,  # 24 hours
    num_output_times=24
)

solver = SWESolver(config=config)

# ... (setup bathymetry and initial conditions as above)

# Define hurricane wind forcing
# Realistic hurricane approach and peak
def hurricane_wind_x(t):
    t_approach = 3600   # Storm approaches for 1 hour
    t_peak = 7200       # Peak winds at 2 hours
    t_decay = 43200     # Storm decays over 12 hours
    
    if t < t_approach:
        # Ramp up initial circulation
        return 30 * (t / t_approach)**1.5
    elif t < t_peak:
        # Strengthen to maximum
        return 30 + 50 * ((t - t_approach) / (t_peak - t_approach))
    else:
        # Decay after peak
        decay_time = min(t - t_peak, t_decay)
        return 80 * np.exp(-decay_time / 10800)  # 3-hour e-decay

def hurricane_wind_y(t):
    # Perpendicular wind component (similar pattern)
    return 0.5 * hurricane_wind_x(t)

solver.set_wind_forcing(
    wind_x=hurricane_wind_x,
    wind_y=hurricane_wind_y,
    ramp_time=300
)

# ... setup and solve
solver.setup_solver()
solutions = solver.solve()
```

---

## Working with Station Data CSV

### Filter and Interpolate Observations

```python
import physrag
import pandas as pd

extent = (-87.25, -87.05, 30.2, 30.4)

# Filter observations (assumes columns: station_id, longitude, latitude, water_level_m, timestamp)
obs = pd.read_csv('data/noaa_stations_2024.csv')
obs_filtered = obs[
    (obs['longitude'] >= extent[0]) & (obs['longitude'] <= extent[1]) &
    (obs['latitude'] >= extent[2]) & (obs['latitude'] <= extent[3])
]

print(f"Filtered to {len(obs_filtered)} stations in extent")

# Use for initial condition as shown above
```

---

## Validation Against Observations

### Compare Simulation with Buoy Data

```python
import numpy as np
import physrag

# ... (run simulation to get `solutions`)

# Load observation time series
obs_time = np.array([...])  # seconds from start
obs_elevation = np.array([...])  # meter elevation

# Extract model time series at nearest grid point
i_model, j_model = 25, 25  # Closest to observation location
model_ts = solutions.get_time_series(i_model, j_model, variable='h')

# Compare
rmse = np.sqrt(np.mean((model_ts - obs_elevation)**2))
mae = np.mean(np.abs(model_ts - obs_elevation))

print(f"RMSE: {rmse:.3f} m")
print(f"MAE:  {mae:.3f} m")

# Visualization
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 4))
plt.plot(solutions.time, model_ts, 'b-', label='Model', linewidth=2)
plt.plot(obs_time, obs_elevation, 'r.', label='Observations', markersize=4)
plt.xlabel('Time (seconds)')
plt.ylabel('Water Elevation (m)')
plt.legend()
plt.title('Model vs Observation')
plt.grid(True)
plt.tight_layout()
plt.savefig('validation.png', dpi=150)
plt.show()
```

---

## Parallel Execution with MPI

### Distribute Computation Across Processors

```python
import physrag
from physrag.config import SimulationConfig
from physrag.solver import SWESolver

# Enable MPI
config = SimulationConfig(
    lon_range=(-87.25, -87.05),
    lat_range=(30.2, 30.4),
    nx=200,  # Higher resolution
    ny=200,
    t_end=3600,
    num_output_times=50,
    use_mpi=True,
    num_processors=4  # Use 4 processors
)

solver = SWESolver(config=config)

# ... setup bathymetry, initial condition, wind ...

solver.setup_solver()
solutions = solver.solve()

print(f"Parallel simulation complete: {solutions.h.shape}")
```

**Run with:**
```bash
mpirun -np 4 python your_script.py
```

---

## Sensitivity Analysis

### Perturb Parameters to Test Robustness

```python
import numpy as np
import physrag
from physrag.config import SimulationConfig
from physrag.solver import SWESolver

# Base configuration
extent = (-87.25, -87.05, 30.2, 30.4)
base_config = SimulationConfig(
    lon_range=extent[:2],
    lat_range=extent[2:],
    nx=50, ny=50,
    t_end=3600,
    cfl=0.9
)

# Perturb bathymetry
depth_factors = [0.9, 1.0, 1.1]  # ±10% depth variation
results = {}

for factor in depth_factors:
    config = SimulationConfig(**{**base_config.__dict__, 'cfl': 0.9})
    solver = SWESolver(config=config)
    
    # Load bathymetry and scale
    bathymetry *= factor
    solver.set_bathymetry(bathymetry)
    
    # ... setup and solve
    solver.setup_solver()
    solutions = solver.solve()
    
    results[f'depth_x{factor}'] = solutions
    print(f"Completed sensitivity test: depth × {factor}")

# Compare maximum elevations
for label, sol in results.items():
    max_elev = sol.h.max()
    print(f"{label:15}: max elevation = {max_elev:.3f} m")
```

---

## Exporting Results

### Save to NetCDF for analysis and sharing

```python
import physrag

# ... run simulation to get `solutions` ...

# Export full solution
solutions.export_netcdf('simulation_results.nc')

# Export just key fields for visualization
import netCDF4 as nc4
    extent=(-87.23, -87.09, 30.20, 30.40),
    lat_col="latitude_decimal_degrees",
    lon_col="longitude_decimal_degrees",
    columns=[
        "station_name",
        "water_level_m_mllw",
        "wind_speed_m_per_s",
        "temperature_c",
    ]
)

print(f"Found {len(df)} stations in region")
print(df.groupby('station_name').size())
```

### Temporal and Spatial Filtering

```python
import physrag

# Filter by both space and time
df = physrag.rag_data_retrieval.read_csv_extent(
    csv_path="data/weather_timeseries.csv",
    extent=(-87.23, -87.09, 30.20, 30.40),
    lat_col="lat",
    lon_col="lon",
    timestamp_col="timestamp_utc_iso8601",
    start_time="2024-02-01T00:00:00Z",
    end_time="2024-02-05T00:00:00Z",
    columns=["station_name", "water_level_m", "wind_speed_m_per_s"]
)

print(f"Data from {df['timestamp_utc_iso8601'].min()} to {df['timestamp_utc_iso8601'].max()}")
```

### Aggregate by Location

```python
import physrag

df = physrag.rag_data_retrieval.read_csv_extent(
    csv_path="data/weather.csv",
    extent=(-87.23, -87.09, 30.20, 30.40),
    lat_col="latitude_decimal_degrees",
    lon_col="longitude_decimal_degrees",
    columns=["latitude_decimal_degrees", "longitude_decimal_degrees", "water_level_m_mllw"]
)

# Aggregate multiple measurements at same location
aggregated = df.groupby(["longitude_decimal_degrees", "latitude_decimal_degrees"], as_index=False).agg({
    "water_level_m_mllw": ["mean", "std", "count"]
})

print(f"Unique locations: {len(aggregated)}")
print(aggregated.head())
```

---

## Data Interpolation

### Simple Grid Interpolation

```python
import physrag
import numpy as np
import pandas as pd

# Load measurement data
df = pd.read_csv("measurements.csv")  # columns: lon, lat, value

# Create interpolator
interp = physrag.data_interpolation.SparseDataInterpolator(
    x=df['lon'].values,
    y=df['lat'].values,
    values=df['value'].values
)

# Create regular grid
lon_grid = np.linspace(df['lon'].min(), df['lon'].max(), 100)
lat_grid = np.linspace(df['lat'].min(), df['lat'].max(), 100)
lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

# Interpolate
interpolated, uncertainties = interp.interpolate(
    lon_mesh.flatten(),
    lat_mesh.flatten()
)

# Reshape to grid
data_grid = interpolated.reshape(lon_mesh.shape)
uncert_grid = uncertainties.reshape(lon_mesh.shape)

print(f"Interpolated data shape: {data_grid.shape}")
print(f"Mean uncertainty: {uncert_grid.mean():.4f}")
```

---

## Visualization

### Animate Water Surface Elevation

```python
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as patches
import cartopy.crs as ccrs

# ... (run simulation to get `solutions`)

fig = plt.figure(figsize=(12, 8))

# Create GeoAxes
ax = fig.add_subplot(111, projection=ccrs.PlateCarree())
ax.coastlines()

def update_frame(framenum):
    ax.clear()
    
    # Plot bathymetry as background
    cf = ax.contourf(
        solutions.coord_meshgrid[0],
        solutions.coord_meshgrid[1],
        solutions.bathymetry,
        cmap='Greys_r',
        alpha=0.3,
        levels=20
    )
    
    # Plot water elevation
    h_plot = ax.contourf(
        solutions.coord_meshgrid[0],
        solutions.coord_meshgrid[1],
        solutions.h[framenum],
        cmap='Blues',
        levels=15,
        vmin=0,
        vmax=solutions.h.max()
    )
    
    ax.set_title(f'Water Elevation at t = {solutions.time[framenum]:.0f}s')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    plt.colorbar(h_plot, ax=ax, label='Elevation (m)')

anim = animation.FuncAnimation(
    fig, update_frame,
    frames=len(solutions.time),
    interval=100, repeat=True
)

plt.tight_layout()
anim.save('simulation.gif', writer='pillow', fps=10)
plt.show()
```

---

### Static Contour Plot

```python
import matplotlib.pyplot as plt
import numpy as np

# Plot max elevation over simulation
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Max elevation
max_elev = solutions.h.max(axis=0)
cf = axes[0].contourf(
    solutions.coord_meshgrid[0],
    solutions.coord_meshgrid[1],
    max_elev,
    cmap='YlOrRd',
    levels=20
)
axes[0].set_title('Maximum Water Elevation')
axes[0].set_xlabel('Longitude')
axes[0].set_ylabel('Latitude')
plt.colorbar(cf, ax=axes[0], label='Elevation (m)')

# Final inundation depth
inundation = solutions.h[-1] - solutions.bathymetry
cf = axes[1].contourf(
    solutions.coord_meshgrid[0],
    solutions.coord_meshgrid[1],
    inundation,
    cmap='Blues_r',
    levels=20,
    vmin=0
)
axes[1].set_title('Final Inundation Depth')
axes[1].set_xlabel('Longitude')
axes[1].set_ylabel('Latitude')
plt.colorbar(cf, ax=axes[1], label='Depth (m)')

plt.tight_layout()
plt.savefig('elevation_analysis.png', dpi=150, bbox_inches='tight')
plt.show()
```

---

## Advanced: Custom Initial Conditions

### Tsunami Wave Profile

```python
import numpy as np

# Submarine earthquake generates wave packet
def tsunami_initial_condition(x, y, extent, magnitude=7.0):
    """
    Gaussian wave packet from offshore earthquake.
    Magnitude parameter scales amplitude.
    """
    x0, y0 = -87.2, 30.3  # Epicenter
    sigma = 0.05  # Wave extent in degrees
    amplitude = 0.5 * (magnitude - 6.0)  # Amplitude from magnitude
    
    distance = np.sqrt((x - x0)**2 + (y - y0)**2)
    h = amplitude * np.exp(-distance**2 / (2 * sigma**2))
    
    return h

# Use in simulation
h0 = tsunami_initial_condition(x_mg, y_mg, extent, magnitude=7.5)
solver.set_initial_condition(h0)
```

---

## Performance Optimization

### Memory Efficient Sparse Grids

For large domains, use coarse initial grids with refinement:

```python
# Start with coarse grid
config_coarse = SimulationConfig(
    lon_range=extent[:2],
    lat_range=extent[2:],
    nx=50, ny=50,
    t_end=1800
)

solver_coarse = SWESolver(config=config_coarse)
solutions_coarse = solver_coarse.solve()

# Refine to fine grid for detailed analysis
config_fine = SimulationConfig(
    lon_range=extent[:2],
    lat_range=extent[2:],
    nx=200, ny=200,  # 4× finer
    t_end=1800
)

# Use coarse solution as initial condition (interpolated)
interp = SparseDataInterpolator(
    x=solutions_coarse.coord_meshgrid[0].flatten(),
    y=solutions_coarse.coord_meshgrid[1].flatten(),
    values=solutions_coarse.h[-1].flatten()  # Final state from coarse run
)

solver_fine = SWESolver(config=config_fine)
h0_fine, _ = interp.interpolate(
    fine_x_mg.flatten(),
    fine_y_mg.flatten()
)
solver_fine.set_initial_condition(h0_fine.reshape(fine_x_mg.shape))
```

---

## Troubleshooting Common Issues

### Simulation Diverges (NaN values)

**Cause:** CFL number too high or bathymetry discontinuities

**Solution:**
```python
# Reduce CFL
config.cfl = 0.5  # Lower from 0.9

# Smooth bathymetry
from scipy.ndimage import gaussian_filter
bathymetry_smooth = gaussian_filter(bathymetry, sigma=2)
solver.set_bathymetry(bathymetry_smooth)
```

### Memory Error on Large Grids

**Cause:** Too many grid points or output times

**Solution:**
```python
# Reduce grid size
config.nx = 100  # Instead of 500
config.ny = 100

# Reduce output frequency
config.num_output_times = 5  # Instead of 100

# Use coarse-then-fine approach (see above)
```

### OPeNDAP Connection Timeout

**Cause:** Server slow or unavailable

**Solution:**
```python
# Download GEBCO once, cache locally
from physrag.bathymetry_retrieval import GEBCOBathymetryProvider

provider = GEBCOBathymetryProvider(cache_dir='./gebco_cache')
bathymetry = provider.get_bathymetry(extent)  # Cached on subsequent calls
```
```

### Combining Interpolation with GEBCO Bathymetry

```python
import physrag
import numpy as np

extent = (-87.23, -87.09, 30.20, 30.40)

# Get bathymetry
bathy_df = physrag.bathymetry_retrieval.download_gebco_ascii(extent=extent)

# Get water level measurements
water_df = physrag.rag_data_retrieval.read_csv_extent(
    csv_path="water_levels.csv",
    extent=extent,
    lat_col="latitude",
    lon_col="longitude",
    columns=["longitude", "latitude", "water_level_m"]
)

# Create water level interpolator
water_interp = physrag.data_interpolation.SparseDataInterpolator(
    x=water_df['longitude'].values,
    y=water_df['latitude'].values,
    values=water_df['water_level_m'].values
)

# Create grid from bathymetry
lon_grid = np.linspace(extent[0], extent[1], 50)
lat_grid = np.linspace(extent[2], extent[3], 50)
lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

# Interpolate water levels
water_level, uncert = water_interp.interpolate(
    lon_mesh.flatten(),
    lat_mesh.flatten()
)

# Get bathymetry at same grid points
from scipy.interpolate import griddata
bathymetry = griddata(
    (bathy_df['Longitude'], bathy_df['Latitude']),
    bathy_df['Elevation'],
    (lon_mesh.flatten(), lat_mesh.flatten()),
    method='linear'
)

print(f"Water level range: {water_level.min():.2f} to {water_level.max():.2f} m")
print(f"Bathymetry range: {bathymetry.min():.2f} to {bathymetry.max():.2f} m")
```

### Validation: Leave-One-Out Cross Validation

```python
import physrag
import numpy as np

# Load data with more points than needed
df = pd.read_csv("measurements.csv")

# Leave-one-out cross validation
errors = []
for i in range(len(df)):
    # Exclude point i
    mask = np.arange(len(df)) != i
    train_x = df.iloc[mask, 0].values
    train_y = df.iloc[mask, 1].values
    train_val = df.iloc[mask, 2].values
    
    # Create interpolator without point i
    interp = physrag.data_interpolation.SparseDataInterpolator(
        x=train_x,
        y=train_y,
        values=train_val
    )
    
    # Predict at point i
    pred, _ = interp.interpolate(
        df.iloc[i, 0:1].values,
        df.iloc[i, 1:2].values
    )
    
    error = abs(pred[0] - df.iloc[i, 2])
    errors.append(error)

mean_error = np.mean(errors)
std_error = np.std(errors)
print(f"Leave-one-out: mean error = {mean_error:.4f}, std = {std_error:.4f}")
```

---

## Advanced: Building Simulation Input

### Complete Workflow: prepare SWE input

```python
import physrag
from physrag.integrations.tidalflow_providers import (
    BathymetryFromGEBCO,
    InitialConditionInterpolationProvider,
)
import numpy as np

# Define simulation domain
extent = (-87.23, -87.09, 30.20, 30.40)
lon_range = (extent[0], extent[1])
lat_range = (extent[2], extent[3])

# Step 1: Load and filter weather/water level data
df_weather = physrag.rag_data_retrieval.read_csv_extent(
    csv_path="data/2024-02-02.csv",
    extent=extent,
    lat_col="latitude_decimal_degrees",
    lon_col="longitude_decimal_degrees",
    columns=[
        "station_name",
        "water_level_m_mllw",
        "wind_speed_m_per_s",
    ],
    timestamp_col="timestamp_utc_iso8601",
)

# Step 2: Aggregate by location (multiple measurements per station)
df_weather = df_weather.groupby(
    ["latitude_decimal_degrees", "longitude_decimal_degrees"],
    as_index=False
).agg({"water_level_m_mllw": "mean", "wind_speed_m_per_s": "mean"})

print(f"Using {len(df_weather)} weather stations")

# Step 3: Create bathymetry provider
bath_provider = BathymetryFromGEBCO(extent=extent, keep_csv=True)

# Step 4: Create water level provider
water_provider = WaterLevelInterpolationProvider(
    lon=df_weather["longitude_decimal_degrees"].values,
    lat=df_weather["latitude_decimal_degrees"].values,
    values=df_weather["water_level_m_mllw"].values,
)

# Step 5: Use with tidalflow
import tidalflow

config = tidalflow.config.SimulationConfig(
    lon_range=lon_range,
    lat_range=lat_range,
    nx=40,
    ny=40,
    t_final=1000.0,
    dt=1.0,
    output_dir="output_swe",
)

solver = tidalflow.solver.SWESolver(
    config=config,
    bathymetry_provider=bath_provider,
    ic_provider=water_provider,
)

solver.initialize_data_from_providers()
result = solver.solve()

print(f"Simulation complete: solution shape {result.solution.shape}")
```

---

## Error Handling & Debugging

### Check Data Quality

```python
import physrag
import numpy as np

df = physrag.bathymetry_retrieval.download_gebco_ascii(
    extent=(-87.23, -87.09, 30.20, 30.40)
)

# Check for NaN values
print(f"NaN values: {df.isna().sum().sum()}")

# Check coordinate ranges
print(f"Lon range: {df['Longitude'].min():.4f} to {df['Longitude'].max():.4f}")
print(f"Lat range: {df['Latitude'].min():.4f} to {df['Latitude'].max():.4f}")

# Check data distribution
print(f"Elevation: {df['Elevation'].min():.2f}m to {df['Elevation'].max():.2f}m")
print(f"  Mean: {df['Elevation'].mean():.2f}m, Std: {df['Elevation'].std():.2f}m")
```

### Validate Interpolation Setup

```python
import physrag
import numpy as np

# Check measurement data
print(f"Number of measurements: {len(x)}")
print(f"Extent: [{x.min()}, {x.max()}] x [{y.min()}, {y.max()}]")

if len(np.unique(x)) < 3 or len(np.unique(y)) < 3:
    print("WARNING: Very few unique locations; interpolation may be unreliable")

# Check for duplicate points
duplicates = len(x) - len(np.unique(list(zip(x, y))))
if duplicates > 0:
    print(f"WARNING: {duplicates} duplicate measurement points")

# Create interpolator and test
interp = physrag.data_interpolation.SparseDataInterpolator(x, y, values)
test_val, test_uncert = interp.interpolate(x[:1], y[:1])
print(f"Interpolator working; test uncertainty: {test_uncert[0]:.4f}")
```

---

## Performance Tips

### Large Datasets

```python
import physrag

# For very large CSV files, filter first to reduce memory
extent = (-87.23, -87.09, 30.20, 30.40)

# Load only the extent you need
df_small = physrag.rag_data_retrieval.read_csv_extent(
    csv_path="huge_file.csv",
    extent=extent,  # Filters before loading into memory
    lat_col="lat",
    lon_col="lon"
)

# Now work with smaller dataset
print(f"Loaded {len(df_small)} points from potentially much larger file")
```

### Reuse Interpolators

```python
# Bad: Creating interpolator multiple times
for extent in extents:
    interp = physrag.data_interpolation.SparseDataInterpolator(x, y, values)
    result = interp.interpolate(...)

# Good: Create once, reuse
interp = physrag.data_interpolation.SparseDataInterpolator(x, y, values)
for extent in extents:
    result = interp.interpolate(...)
```

### Chunked Interpolation

```python
import physrag
import numpy as np

# For very large grids, interpolate in chunks
interp = physrag.data_interpolation.SparseDataInterpolator(x, y, values)

lon_grid = np.linspace(-87.23, -87.09, 1000)
lat_grid = np.linspace(30.20, 30.40, 1000)

# Process in 100x100 chunks
chunk_size = 100
results = []

for i in range(0, len(lon_grid), chunk_size):
    for j in range(0, len(lat_grid), chunk_size):
        lon_chunk = lon_grid[i:i+chunk_size]
        lat_chunk = lat_grid[j:j+chunk_size]
        lon_m, lat_m = np.meshgrid(lon_chunk, lat_chunk)
        
        vals, uncert = interp.interpolate(lon_m.flatten(), lat_m.flatten())
        results.append(vals.reshape(lon_m.shape))

result = np.concatenate(results)
```
