# SWE Results

Guide to working with simulation results and solution data.

## Overview

After running a SWE simulation, results are stored on disk in PyClaw's native format. PhysRAG-SWE provides utilities to read, analyze, and visualize results.

---

## Solution Output Files

### Directory Structure

```
output_simulation/
├── claw.pkl0000          # Frame 0 solution
├── claw.pkl0001          # Frame 1 solution
├── claw.pkl0002          # Frame 2 solution
├── ...
├── claw.ptc0000          # Frame 0 parameters
├── claw.ptc0000.info     # Frame 0 info
├── claw.ptc0001          # Frame 1 parameters
├── claw.ptc0001.info     # Frame 1 info
├── ...
├── coord_meshgrid.npy    # Grid coordinates (2, ny, nx)
├── bathymetry.npy        # Bathymetry (ny, nx)
└── config.json           # Simulation configuration
```

### File Formats

| File | Format | Contents |
|------|--------|----------|
| `claw.pkl####` | PyClaw pickle | State variables (h, hu, hv) at time t_#### |
| `claw.ptc####` | PyClaw parameters | Solution metadata and parameters |
| `coord_meshgrid.npy` | NumPy array | Grid coordinates |
| `bathymetry.npy` | NumPy array | Bathymetry on grid |
| `config.json` | JSON | Simulation configuration |

---

## Reading Solutions

### Basic Usage

```python
import physrag
import numpy as np

# Read all solutions
result = physrag.utils.read_solutions(
    outdir="output_simulation",
    frames_list=None,  # None = all frames
)

# Extract components
solutions = result["solutions"]      # (n_frames, 3, ny, nx)
bathymetry = result["bathymetry"]   # (ny, nx)
lon_grid, lat_grid = result["meshgrid"]
times = result["times"]             # (n_frames,)
frame_indices = result["frames"]    # [0, 1, 2, ...]

print(f"Loaded {len(solutions)} frames")
print(f"Solution shape: {solutions.shape}")
print(f"Time range: {times[0]:.1f} to {times[-1]:.1f} seconds")
```

### Selective Frame Reading

```python
# Read specific frames
result = physrag.utils.read_solutions(
    outdir="output_simulation",
    frames_list=[0, 10, 20, 30],  # Read frames 0, 10, 20, 30
)

# Read every N-th frame
frames_every_10 = list(range(0, 100, 10))
result = physrag.utils.read_solutions(
    outdir="output_simulation",
    frames_list=frames_every_10,
)
```

### Extracting Solution Components

```python
# Access individual frames
frame_idx = 10
h = solutions[frame_idx, 0, :, :]       # Water depth (m)
hu = solutions[frame_idx, 1, :, :]      # x-momentum (m²/s)
hv = solutions[frame_idx, 2, :, :]      # y-momentum (m²/s)

# Calculate velocities
u = np.where(h > 1e-6, hu / h, 0)
v = np.where(h > 1e-6, hv / h, 0)
speed = np.sqrt(u**2 + v**2)

# Water surface elevation
eta = h + bathymetry  # Free surface = depth + bathymetry

# Get time for this frame
t = times[frame_idx]
```

---

## SWEResult Container

Result data container:

```python
from physrag.solver import SWEResult

# Create result object
result = SWEResult(
    solutions=solutions_array,      # (n_frames, 3, ny, nx)
    bathymetry=bathymetry_array,   # (ny, nx)
    coord_meshgrid=(lon_grid, lat_grid),
    times=times_array,              # (n_frames,)
    config=config_object,
    frame_indices=frame_list,
)

# Access fields
h_all = result.solutions[:, 0, :, :]
t = result.times
bathy = result.bathymetry
lon, lat = result.coord_meshgrid
cfg = result.config

# Save for later
result.save("saved_result.pkl")

# Load later
result_loaded = SWEResult.load("saved_result.pkl")
```

---

## Analysis & Statistics

### Time Series Analysis

```python
import matplotlib.pyplot as plt

# Track maximum water depth over time
h_max_time = np.max(solutions[:, 0, :, :], axis=(1, 2))

plt.figure(figsize=(12, 4))
plt.plot(times, h_max_time, 'b-', linewidth=2)
plt.xlabel('Time (s)')
plt.ylabel('Maximum Water Depth (m)')
plt.title('Water Depth Evolution')
plt.grid(True, alpha=0.3)
plt.show()

# Find peak and timing
peak_depth = h_max_time.max()
peak_time = times[np.argmax(h_max_time)]
print(f"Peak depth: {peak_depth:.2f} m at t = {peak_time:.1f} s")
```

### Spatial Statistics

```python
# Final frame statistics
h_final = solutions[-1, 0, :, :]
u_final = np.where(h_final > 1e-6, solutions[-1, 1, :, :] / h_final, 0)
v_final = np.where(h_final > 1e-6, solutions[-1, 2, :, :] / h_final, 0)

print("Final Frame Statistics:")
print(f"  Water depth: min={h_final.min():.3f}, mean={h_final.mean():.3f}, max={h_final.max():.3f} m")
print(f"  Wet area: {(h_final > 1e-3).sum() / h_final.size * 100:.1f}%")

velocity_mag = np.sqrt(u_final**2 + v_final**2)
print(f"  Velocity: min={velocity_mag.min():.3f}, mean={velocity_mag[h_final > 1e-3].mean():.3f}, max={velocity_mag.max():.3f} m/s")
```

### Inundation Analysis

```python
# Find maximum inundation extent
h_max_spatial = np.max(solutions[:, 0, :, :], axis=0)

# Areas with h > threshold
threshold = 0.1  # 10 cm
inundated = h_max_spatial > threshold

# Inundated area extent
inundated_lon = lon_grid[inundated]
inundated_lat = lat_grid[inundated]

print(f"Inundation extent:")
print(f"  Longitude: {inundated_lon.min():.4f} to {inundated_lon.max():.4f}")
print(f"  Latitude: {inundated_lat.min():.4f} to {inundated_lat.max():.4f}")
print(f"  Area: {inundated.sum()} grid cells")
```

---

## Visualization

### 2D Contour Plots

```python
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Final water depth
frame_idx = -1
h = solutions[frame_idx, 0, :, :]

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Water depth
cf = axes[0].contourf(lon_grid, lat_grid, h, levels=20, cmap='Blues')
axes[0].set_xlabel('Longitude')
axes[0].set_ylabel('Latitude')
axes[0].set_title(f'Water Depth at t={times[frame_idx]:.1f} s')
plt.colorbar(cf, ax=axes[0], label='Depth (m)')

# Velocity field
u = np.where(h > 1e-6, solutions[frame_idx, 1, :, :] / h, 0)
v = np.where(h > 1e-6, solutions[frame_idx, 2, :, :] / h, 0)
speed = np.sqrt(u**2 + v**2)

cf = axes[1].contourf(lon_grid, lat_grid, speed, levels=20, cmap='RdYlBu_r')
axes[1].quiver(lon_grid[::3, ::3], lat_grid[::3, ::3],
               u[::3, ::3], v[::3, ::3], scale=200)
axes[1].set_xlabel('Longitude')
axes[1].set_ylabel('Latitude')
axes[1].set_title(f'Velocity Field at t={times[frame_idx]:.1f} s')
plt.colorbar(cf, ax=axes[1], label='Speed (m/s)')

plt.tight_layout()
plt.show()
```

### Animation

```python
import physrag

# Create animation of all frames
physrag.utils.animate_solution(
    output_path="output_simulation",
    frames=None,              # All frames
    wave_treshold=1e-2,      # Minimum depth to display
    interval=100,             # Milliseconds between frames
    save=False,               # Don't save to file
)
```

### 3D Surface Plots

```python
from mpl_toolkits.mplot3d import Axes3D

frame_idx = 10
h = solutions[frame_idx, 0, :, :]

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# Plot surface
surf = ax.plot_surface(lon_grid, lat_grid, h, cmap='Blues', alpha=0.8)

ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_zlabel('Water Depth (m)')
ax.set_title(f'Water Surface at t={times[frame_idx]:.1f} s')

plt.colorbar(surf, ax=ax, label='Depth (m)')
plt.show()
```

---

## Comparison & Validation

### Compare with Observations

```python
import pandas as pd

# Load observations
obs = pd.read_csv("data/tide_observations.csv")

# Extract modeled water level at observation locations
# (requires spatial interpolation)
from scipy.interpolate import griddata

h_final = solutions[-1, 0, :, :]

h_at_obs = griddata(
    (lon_grid.flatten(), lat_grid.flatten()),
    h_final.flatten(),
    (obs['longitude'].values, obs['latitude'].values),
    method='linear'
)

# Compare
errors = h_at_obs - obs['water_level'].values
rmse = np.sqrt(np.mean(errors**2))
mae = np.mean(np.abs(errors))

print(f"Model-Observation Comparison:")
print(f"  RMSE: {rmse:.3f} m")
print(f"  MAE: {mae:.3f} m")
print(f"  Bias: {errors.mean():.3f} m")

# Scatter plot
plt.figure(figsize=(8, 6))
plt.scatter(obs['water_level'].values, h_at_obs, alpha=0.5)
plt.plot([obs['water_level'].min(), obs['water_level'].max()],
         [obs['water_level'].min(), obs['water_level'].max()], 'r--', label='Perfect match')
plt.xlabel('Observed Water Level (m)')
plt.ylabel('Modeled Water Level (m)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

### Compare Multiple Simulations

```python
# Run with different parameters and compare
results = {}

for dt_test in [0.5, 1.0, 2.0]:
    config = physrag.config.SimulationConfig(
        # ... other parameters
        dt=dt_test,
    )
    solver = physrag.solver.SWESolver(config=config)
    # ... setup ...
    solver.setup_solver()
    solutions = solver.solve()
    results[f"dt={dt_test}"] = solutions

# Compare final frames
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

for idx, (label, solutions) in enumerate(results.items()):
    h_final = solutions[-1, 0, :, :]
    cf = axes[idx].contourf(lon_grid, lat_grid, h_final, levels=20, cmap='Blues')
    axes[idx].set_title(label)
    plt.colorbar(cf, ax=axes[idx])

plt.suptitle('Comparison of Different Time Steps')
plt.show()
```

---

## Exporting Results

### Save as NetCDF

```python
import xarray as xr

# Create xarray Dataset
ds = xr.Dataset(
    {
        'h': (['time', 'y', 'x'], solutions[:, 0, :, :]),
        'hu': (['time', 'y', 'x'], solutions[:, 1, :, :]),
        'hv': (['time', 'y', 'x'], solutions[:, 2, :, :]),
        'bathymetry': (['y', 'x'], bathymetry),
    },
    coords={
        'time': times,
        'y': np.arange(config.ny),
        'x': np.arange(config.nx),
        'longitude': (['y', 'x'], lon_grid),
        'latitude': (['y', 'x'], lat_grid),
    }
)

# Add attributes
ds.attrs['description'] = 'SWE simulation results'
ds.attrs['config_file'] = 'simulation_config.json'

# Save
ds.to_netcdf('results.nc')
```

### Save as HDF5

```python
import h5py

with h5py.File('results.h5', 'w') as f:
    # Create datasets
    f.create_dataset('solutions', data=solutions)
    f.create_dataset('bathymetry', data=bathymetry)
    f.create_dataset('times', data=times)
    f.create_dataset('lon_grid', data=lon_grid)
    f.create_dataset('lat_grid', data=lat_grid)
    
    # Add metadata
    f.attrs['simulation_time_final'] = times[-1]
    f.attrs['grid_nx'] = config.nx
    f.attrs['grid_ny'] = config.ny
```

### Export for External Software

```python
import pandas as pd

# Export final state as GIS-compatible format
h_final = solutions[-1, 0, :, :]
u_final = np.where(h_final > 1e-6, solutions[-1, 1, :, :] / h_final, 0)
v_final = np.where(h_final > 1e-6, solutions[-1, 2, :, :] / h_final, 0)

# Create DataFrame for each grid point
data = {
    'longitude': lon_grid.flatten(),
    'latitude': lat_grid.flatten(),
    'water_depth': h_final.flatten(),
    'velocity_u': u_final.flatten(),
    'velocity_v': v_final.flatten(),
    'bathymetry': bathymetry.flatten(),
}

df = pd.DataFrame(data)
df.to_csv('solution_final.csv', index=False)

# GeoJSON for use in GIS tools
import geojson

features = []
for idx, row in df.iterrows():
    feature = geojson.Feature(
        geometry=geojson.Point((row['longitude'], row['latitude'])),
        properties={
            'depth': row['water_depth'],
            'u': row['velocity_u'],
            'v': row['velocity_v'],
        }
    )
    features.append(feature)

fc = geojson.FeatureCollection(features)

with open('solution_final.geojson', 'w') as f:
    geojson.dump(fc, f)
```

---

## Advanced Analysis

### Spectral Analysis

```python
from scipy.fft import fft

# Fourier transform of time series
h_max_time = np.max(solutions[:, 0, :, :], axis=(1, 2))

# Remove trend
from scipy.signal import detrend
h_detrended = detrend(h_max_time)

# FFT
fft_vals = fft(h_detrended)
freqs = np.fft.fftfreq(len(h_detrended), d=times[1] - times[0])

# Power spectrum
power = np.abs(fft_vals)**2

# Plot
plt.figure(figsize=(12, 4))
plt.semilogy(freqs[1:len(freqs)//2], power[1:len(freqs)//2])
plt.xlabel('Frequency (Hz)')
plt.ylabel('Power')
plt.title('Power Spectrum of Water Depth')
plt.grid(True, alpha=0.3)
plt.show()
```

### Energy Analysis

```python
# Kinetic energy time series
ke_time = []

for frame_idx in range(len(solutions)):
    h = solutions[frame_idx, 0, :, :]
    hu = solutions[frame_idx, 1, :, :]
    hv = solutions[frame_idx, 2, :, :]
    
    u = np.where(h > 1e-6, hu / h, 0)
    v = np.where(h > 1e-6, hv / h, 0)
    
    ke = 0.5 * np.sum(h * (u**2 + v**2))
    ke_time.append(ke)

plt.figure(figsize=(12, 4))
plt.plot(times, ke_time)
plt.xlabel('Time (s)')
plt.ylabel('Kinetic Energy (J)')
plt.title('Kinetic Energy Evolution')
plt.grid(True, alpha=0.3)
plt.show()
```

---

## References

- **PyClaw Output**: http://www.clawpack.org/pyclaw/
- **Xarray**: http://xarray.pydata.org/
- **Visualization**: Matplotlib, Cartopy documentation

---
