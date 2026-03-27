# Usage Guides

Common patterns and examples for using physrag.

## Working with Bathymetry Data

### Download and Cache Locally

```python
import physrag

extent = (-87.23, -87.09, 30.20, 30.40)

# Download GEBCO data and save as CSV
df, csv_path, _ = physrag.bathymetry_retrieval.get_gebco_data(
    extent=extent,
    keep_csv=True,
    keep_txt=False
)

print(f"Data saved to: {csv_path}")
print(f"Data shape: {df.shape}")
print(df.head())
```

### Filter Bathymetry by Depth

```python
import physrag

df = physrag.bathymetry_retrieval.download_gebco_ascii(
    extent=(-87.23, -87.09, 30.20, 30.40)
)

# Get underwater points
underwater = df[df['Elevation'] < 0]
print(f"Underwater points: {len(underwater)}")

# Get shallow areas (0-10m depth)
shallow = df[(df['Elevation'] >= -10) & (df['Elevation'] < 0)]
print(f"Shallow areas: {len(shallow)}")
```

### Compare Multiple Extents

```python
import physrag
import pandas as pd

locations = {
    'Pensacola': (-87.23, -87.09, 30.20, 30.40),
    'Virginia Key': (-80.18, -80.06, 25.65, 25.93),
}

bathy_data = {}
for name, extent in locations.items():
    df = physrag.bathymetry_retrieval.download_gebco_ascii(extent=extent)
    bathy_data[name] = {
        'mean_depth': df['Elevation'].mean(),
        'max_depth': df['Elevation'].min(),  # min = deepest
        'min_depth': df['Elevation'].max(),  # max = shallowest
        'n_points': len(df),
    }

summary = pd.DataFrame(bathy_data).T
print(summary)
```

---

## Working with CSV Data

### Filter Weather Station Data

```python
import physrag

# Filter weather data to specific geographic region
df = physrag.rag_data_retrieval.read_csv_extent(
    csv_path="data/weather_stations.csv",
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
    WaterLevelInterpolationProvider,
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
