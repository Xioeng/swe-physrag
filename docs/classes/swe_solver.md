# SWE Solver

Comprehensive guide to the SWESolver class for 2D shallow water equations simulations.

## SimulationConfig

Configuration dataclass for SWE simulations:

```python
import physrag

config = physrag.config.SimulationConfig(
    # Domain geometry
    lon_range=(-80.1865, -80.0791),     # Longitude bounds (degrees)
    lat_range=(25.6678, 25.9137),       # Latitude bounds (degrees)
    nx=40,                               # Grid cells in x direction
    ny=40,                               # Grid cells in y direction
    
    # Time stepping
    t_final=1000.0,                      # Final time (seconds)
    dt=1.0,                              # Time step size (seconds)
    
    # Physics parameters
    gravity=9.81,                        # Gravitational acceleration (m/s²)
    
    # Boundary conditions
    bc_lower=(1, 1),                     # [bc_x_lower, bc_y_lower]
    bc_upper=(1, 1),                     # [bc_x_upper, bc_y_upper]
                                         # 0 = wall, 1 = extrap, 2 = periodic
    
    # Output configuration
    output_dir="output_simulation",      # Output directory path
    multiple_output_times=True,          # Save intermediate solutions
    frame_interval=1,                    # Steps between outputs
    
    # Numerical parameters
    cfl_desired=0.9,                     # Target CFL number
    cfl_max=1.0,                         # Maximum CFL number
    max_steps=10000,                     # Maximum simulation steps
)

# Validate configuration
config.validate()

# Save for reproducibility
config.save("config.json")

# Load previously saved config
config_loaded = physrag.config.SimulationConfig.load("config.json")
```

### Configuration Parameters

#### Domain Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `lon_range` | tuple | (lon_min, lon_max) in degrees | Required |
| `lat_range` | tuple | (lat_min, lat_max) in degrees | Required |
| `nx` | int | Number of grid cells in x-direction | Required |
| `ny` | int | Number of grid cells in y-direction | Required |

#### Time Stepping

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `t_final` | float | Simulation end time (seconds) | Required |
| `dt` | float | Time step size (seconds) | Required |
| `max_steps` | int | Maximum simulation steps | 10000 |

#### Physics

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `gravity` | float | Gravitational acceleration (m/s²) | 9.81 |

#### Boundary Conditions

- `0`: Solid wall (reflective)
- `1`: Extrapolation (open boundary)
- `2`: Periodic boundary

```python
# All walls
bc_lower=(0, 0)
bc_upper=(0, 0)

# Open ocean
bc_lower=(1, 1)
bc_upper=(1, 1)

# Coastal domain
bc_lower=(0, 1)  # Wall on x=min, open on y=min
bc_upper=(1, 1)  # Open on x=max, y=max
```

#### Numerical Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `cfl_desired` | float | Target Courant number | 0.9 |
| `cfl_max` | float | Maximum Courant number | 1.0 |

### Validation

Configuration validation checks:

```python
config.validate()

# Checks performed:
# - lon_range[0] < lon_range[1]
# - lat_range[0] < lat_range[1]
# - nx, ny > 0
# - t_final > dt > 0
# - 0 < gravity
# - Valid boundary condition values (0, 1, or 2)
# - 0 < cfl_desired <= cfl_max
```

---

## SWESolver

Main solver class:

```python
import physrag
import numpy as np

# Create configuration
config = physrag.config.SimulationConfig(
    lon_range=(-80.2, -80.0),
    lat_range=(25.6, 25.95),
    nx=40,
    ny=40,
    t_final=1000.0,
    dt=1.0,
    gravity=9.81,
    bc_lower=(1, 1),
    bc_upper=(1, 1),
    output_dir="_output",
)

# Initialize solver
solver = physrag.solver.SWESolver(config=config)

# Grid information
print(f"Grid shape: {solver.nx} x {solver.ny}")
print(f"X coordinates shape: {solver.X_coord.shape}")
print(f"Y coordinates shape: {solver.Y_coord.shape}")
print(f"M solver rank: {solver.rank}")  # MPI rank if using MPI
```

### Setting Bathymetry

```python
# Option 1: Direct array
bathymetry = -10.0 * np.ones((config.ny, config.nx))
solver.set_bathymetry(bathymetry)

# Option 2: From GEBCO
bathymetry = physrag.utils.interpolate_gebco_on_grid(
    X=solver.X_coord,
    Y=solver.Y_coord,
    nc_path="data/gebco_2025.nc"
)
bathymetry[np.isnan(bathymetry)] = 0.0
solver.set_bathymetry(bathymetry)

# Option 3: From provider
provider = physrag.bathymetry_retrieval.GEBCOBathymetryProvider(
    nc_path="data/gebco_2025.nc"
)
bathymetry = provider(solver.X_coord, solver.Y_coord)
solver.set_bathymetry(bathymetry)
```

**Requirements:**
- Array shape must be `(ny, nx)`
- Can contain NaN values for land/missing data
- Negative values = depth below MSL, positive = elevation

### Setting Initial Condition

```python
# Water depth and momentum at t=0
h_init = 0.2 * np.ones((config.ny, config.nx))  # 20 cm depth
hu_init = np.zeros((config.ny, config.nx))      # No x-momentum
hv_init = np.zeros((config.ny, config.nx))      # No y-momentum

initial_condition = np.stack([h_init, hu_init, hv_init], axis=0)

solver.set_initial_condition(initial_condition)

# Example: Gaussian hump
x, y = solver.mapper.coord_to_metric(solver.X_coord, solver.Y_coord)
h_init = 2.0 * np.exp(-0.01 * (x**2 + y**2))
initial_condition = np.stack([h_init, np.zeros_like(h_init), np.zeros_like(h_init)], axis=0)
solver.set_initial_condition(initial_condition)
```

**Requirements:**
- Array shape must be `(3, ny, nx)` for [h, hu, hv]
- h ≥ 0 everywhere (no negative water depths)
- No NaN values allowed

### Wind Forcing

```python
# Constant wind
u_wind = -17.8  # m/s (westward component)
v_wind = 17.8   # m/s (northward component)
solver.set_constant_wind_forcing(u_wind=u_wind, v_wind=v_wind)

# Convert from wind speed and direction
speed_mph = 96  # 96 mph (Category 1 hurricane)
speed_ms = speed_mph * 0.44704
direction_deg = 45  # Direction FROM NE (225°)
direction_rad = np.radians(direction_deg)

u_wind = speed_ms * np.cos(direction_rad)
v_wind = speed_ms * np.sin(direction_rad)
solver.set_constant_wind_forcing(u_wind=u_wind, v_wind=v_wind)
```

**Wind Stress Formulation:**

Wind stress is computed as:
$$\tau = \frac{\rho_a c_d |U| U}{\rho_w}$$

Where:
- $\rho_a = 1.225$ kg/m³: air density
- $\rho_w = 1000$ kg/m³: water density  
- $c_d = 1.3 \times 10^{-3}$: drag coefficient
- $U = (u, v)$: wind velocity (m/s)

### Running Simulation

```python
# Setup solver (initializes PyClaw structures)
solver.setup_solver()

# Run simulation
solutions = solver.solve()

print(f"Simulation complete!")
print(f"Output shape: {solutions.shape}")
# Shape: (n_output_times, 3, ny, nx)
# Dimensions: [time, (h, hu, hv), y, x]
```

### Coordinate Mapping

Convert between geographic (lon/lat) and metric (x/y) coordinates:

```python
# Get mapper
mapper = solver.mapper

# Geographic to metric
x_metric, y_metric = mapper.coord_to_metric(X_coord, Y_coord)

# Metric to geographic
lon, lat = mapper.metric_to_coord(x_metric, y_metric)

# Example: Distance calculation
x1, y1 = mapper.coord_to_metric(-80.1, 25.7)
x2, y2 = mapper.coord_to_metric(-80.15, 25.75)
distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
print(f"Distance: {distance / 1000:.1f} km")
```

---

## Advanced Usage

### Multi-Output Times

Save solution at intermediate times:

```python
config = physrag.config.SimulationConfig(
    # ... other parameters
    multiple_output_times=True,  # Save all output times
    frame_interval=5,            # Save every 5 steps
)

# Read all output
result = physrag.utils.read_solutions(
    outdir=config.output_dir,
    frames_list=None  # Load all frames
)

solutions = result["solutions"]
times = result["times"]
```

### MPI Parallelization

Distribute simulation across multiple processors:

```bash
# Run with 4 processes
mpiexec -n 4 python simulation_script.py
```

```python
# In Python code
solver = physrag.solver.SWESolver(config=config)
print(f"MPI rank: {solver.rank}")
print(f"MPI size: {solver.size}")

# Only rank 0 does I/O
if solver.rank == 0:
    result = physrag.utils.read_solutions(config.output_dir)
```

### Adaptive Time Stepping

Solver automatically adjusts time step based on CFL condition:

```python
config = physrag.config.SimulationConfig(
    # ... other parameters
    cfl_desired=0.8,  # Target CFL number
    cfl_max=0.99,     # Absolute maximum CFL
)

# Solver will automatically reduce dt if CFL exceeded
```

---

## Complete Example

```python
import physrag
import numpy as np

# Configuration
config = physrag.config.SimulationConfig(
    lon_range=(-80.1865, -80.0791),
    lat_range=(25.6678, 25.9137),
    nx=60,
    ny=60,
    t_final=1800.0,
    dt=1.0,
    gravity=9.81,
    bc_lower=(1, 1),
    bc_upper=(1, 1),
    output_dir="output_storm_surge",
    multiple_output_times=True,
    frame_interval=5,
)

# Validate
config.validate()
config.save("simulation_config.json")

# Initialize solver
solver = physrag.solver.SWESolver(config=config)

# Load bathymetry
bathymetry = physrag.utils.interpolate_gebco_on_grid(
    X=solver.X_coord,
    Y=solver.Y_coord,
    nc_path="data/gebco_2025_miami.nc"
)
bathymetry[np.isnan(bathymetry)] = 0.0
solver.set_bathymetry(bathymetry)

# Initial condition from observations
observations = physrag.rag_data_retrieval.read_csv_extent(
    csv_path="data/tide_observations.csv",
    extent=config.lon_range + config.lat_range,
    lat_col="latitude",
    lon_col="longitude"
)

interpolator = physrag.data_interpolation.SparseDataInterpolator(
    x=observations['longitude'].values,
    y=observations['latitude'].values,
    values=observations['water_level'].values,
    method='rbf'
)

h_init_data, _ = interpolator.interpolate(
    solver.X_coord.flatten(),
    solver.Y_coord.flatten()
)
h_init = np.maximum(h_init_data.reshape(solver.X_coord.shape), 0.1)

initial_condition = np.stack([
    h_init,
    np.zeros_like(h_init),
    np.zeros_like(h_init),
], axis=0)
solver.set_initial_condition(initial_condition)

# Hurricane wind (Category 1)
speed_ms = 96 * 0.44704
u_wind = -speed_ms / np.sqrt(2)
v_wind = speed_ms / np.sqrt(2)
solver.set_constant_wind_forcing(u_wind=u_wind, v_wind=v_wind)

# Run
solver.setup_solver()
solutions = solver.solve()

if solver.rank == 0:
    print(f"Simulation complete!")
    print(f"Solutions shape: {solutions.shape}")
    
    # Analyze results
    h_max = solutions[:, 0, :, :].max(axis=(1, 2))
    time_of_max = np.argmax(h_max)
    print(f"Maximum depth: {h_max[time_of_max]:.2f} m")
```

---

## Troubleshooting

### Common Issues

**"Configuration validation failed"**
- Check domain bounds: `lon_range[0] < lon_range[1]`
- Check time: `t_final > dt > 0`
- Check grid: `nx, ny > 0`

**"Bathymetry shape does not match grid"**
- Ensure bathymetry shape is `(ny, nx)`, not `(nx, ny)`

**"Initial condition contains NaN"**
- Check input arrays for NaN
- Interpolate missing values before passing to solver

**"Simulation unstable (NaN output)"**
- Reduce time step `dt`
- Check CFL condition: `dt <= min(dx, dy) / sqrt(g * h_max)`
- Verify initial conditions are physically reasonable

---

## References

- **Shallow Water Equations**: Classical 2D hyperbolic system
- **Riemann Solver**: Uses `shallow_roe_with_efix_2D` from Clawpack
- LeVeque, R. J. (2002). *Finite Volume Methods for Hyperbolic Problems*
- George, D. L. (2006). Finite volume methods and adaptive refinement for tsunami propagation and inundation

---
