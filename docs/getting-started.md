# Getting Started with PhysRAG-SWE

Quick start guide to install and run PhysRAG-SWE for your first simulation.

## Prerequisites

- **Python 3.11+** (3.11, 3.12 recommended)
- **conda** (for managing dependencies)
- **Git** (for cloning the repository)
- **~4GB disk space** (for GEBCO bathymetry data)

---

## Installation

### 1. Create and activate conda environment

```bash
conda env create -f environment.yml
conda activate physrag-swe
```

This creates an isolated environment with all required dependencies:
- clawpack (PyClaw solver)
- numpy, scipy, pandas (numerical computing)
- matplotlib, cartopy (visualization)
- xarray (file I/O)

### 2. Install from source

```bash
git clone https://github.com/yourusername/physrag-swe.git
cd physrag-swe

# Install package in editable mode
pip install -e .
```

### 3. Verify installation

```bash
python -c "import physrag; print(physrag.__version__)"
python -c "import clawpack; print('PyClaw OK')"
```

### 4. (Optional) Development setup

For contributing to PhysRAG-SWE:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Check code style
black physrag/ --check
mypy physrag/
```

---

## Quick Start

### Example 1: Simple Shallow Water Simulation

Create a file `simple_simulation.py`:

```python
import tidalflow
import numpy as np

# Configuration: 10x10 km domain
config = tidalflow.config.SimulationConfig(
    lon_range=(-10.0, 10.0),
    lat_range=(-10.0, 10.0),
    nx=50,
    ny=50,
    t_final=50.0,
    dt=0.5,
    gravity=9.81,
    bc_lower=(0, 0),
    bc_upper=(0, 0),
    output_dir="output_simple",
)

# Initialize solver
solver = tidalflow.solver.SWESolver(config=config)

# Flat seafloor at -10m depth
bathymetry = -10.0 * np.ones((config.ny, config.nx))
solver.set_bathymetry(bathymetry)

# Gaussian hump initial condition
x, y = solver.mapper.coord_to_metric(solver.X_coord, solver.Y_coord)
h_init = 2.0 * np.exp(-0.01 * (x**2 + y**2))
initial_condition = np.stack([
    h_init,
    np.zeros_like(h_init),
    np.zeros_like(h_init),
], axis=0)
solver.set_initial_condition(initial_condition)

# Run simulation
solver.setup_solver()
solutions = solver.solve()

print(f"✓ Simulation complete!")
print(f"  Generated {solutions.shape[0]} output frames")
```

Run it:

```bash
python simple_simulation.py
```

### Example 2: Using Real GEBCO Bathymetry

Create a file `gebco_simulation.py`:

```python
import physrag
import numpy as np

# Miami area
config = physrag.config.SimulationConfig(
    lon_range=(-80.1865, -80.0791),
    lat_range=(25.6678, 25.9137),
    nx=40,
    ny=40,
    t_final=500.0,
    dt=1.0,
    gravity=9.81,
    bc_lower=(1, 1),
    bc_upper=(1, 1),
    output_dir="output_miami",
    multiple_output_times=True,
)

# Initialize solver
solver = physrag.solver.SWESolver(config=config)

# Load GEBCO bathymetry
bathymetry = physrag.utils.interpolate_gebco_on_grid(
    X=solver.X_coord,
    Y=solver.Y_coord,
    nc_path="data/gebco_2025_miami.nc"
)
bathymetry[np.isnan(bathymetry)] = 0.0
solver.set_bathymetry(bathymetry)

# Initial condition: 20 cm water level rise
h_init = 0.2 * np.ones((config.ny, config.nx))
initial_condition = np.stack([
    h_init,
    np.zeros_like(h_init),
    np.zeros_like(h_init),
], axis=0)
solver.set_initial_condition(initial_condition)

# Run simulation
solver.setup_solver()
solutions = solver.solve()

print(f"✓ Simulation complete!")

# Visualize
if solver.rank == 0:
    physrag.utils.animate_solution(
        output_path=config.output_dir,
        frames=None,
        wave_treshold=1e-2,
        save=False,
    )
```

Run it:

```bash
python gebco_simulation.py
```

### Example 3: With Observations Data

Create a file `data_integration_simulation.py`:

```python
import physrag
import numpy as np
import pandas as pd

# Load tide gauge observations
gauge_data = pd.read_csv("data/tide_observations.csv")

# Configuration for simulation
config = physrag.config.SimulationConfig(
    lon_range=(-80.2, -80.0),
    lat_range=(25.6, 25.95),
    nx=40,
    ny=40,
    t_final=600.0,
    dt=1.0,
    gravity=9.81,
    bc_lower=(1, 1),
    bc_upper=(1, 1),
    output_dir="output_with_data",
    multiple_output_times=True,
)

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

# Interpolate observations to grid
interpolator = physrag.data_interpolation.SparseDataInterpolator(
    x=gauge_data['longitude'].values,
    y=gauge_data['latitude'].values,
    values=gauge_data['water_level'].values,
    method='rbf'
)

h_init, uncertainty = interpolator.interpolate(
    solver.X_coord.flatten(),
    solver.Y_coord.flatten()
)
h_init = h_init.reshape(solver.X_coord.shape)
h_init = np.maximum(h_init, 0.1)  # Ensure minimum depth

initial_condition = np.stack([
    h_init,
    np.zeros_like(h_init),
    np.zeros_like(h_init),
], axis=0)
solver.set_initial_condition(initial_condition)

# Run simulation
solver.setup_solver()
solutions = solver.solve()

print(f"✓ Simulation complete!")
print(f"  Initial water level range: {h_init.min():.3f} to {h_init.max():.3f} m")
print(f"  Interpolation uncertainty: ±{uncertainty.mean():.3f} m")
```

---

## Common First Steps

### Download GEBCO Bathymetry

PhysRAG-SWE can fetch GEBCO automatically:

```python
import physrag

extent = (-80.1865, -80.0791, 25.6678, 25.9137)

bathymetry_df = physrag.bathymetry_retrieval.download_gebco_ascii(
    extent=extent
)

print(f"Downloaded {len(bathymetry_df)} bathymetry points")
```

Or manually:

1. Go to https://www.gebco.net/data_and_products/gridded_bathymetry_data/
2. Select your region
3. Download **NetCDF format**
4. Save to `data/gebco_*.nc`

### Prepare Observation Data

Create a CSV file with tide gauge observations:

```csv
station_id,longitude,latitude,water_level,timestamp
G001,-80.18,25.75,0.15,2023-09-01T00:00:00
G002,-80.10,25.70,0.12,2023-09-01T00:00:00
G003,-80.13,25.80,0.18,2023-09-01T00:00:00
```

Load and use:

```python
import pandas as pd
import physrag

observations = pd.read_csv("data/tide_observations.csv")

# Filter by geographic extent
observations = physrag.rag_data_retrieval.read_csv_extent(
    csv_path="data/tide_observations.csv",
    extent=(-80.2, -80.0, 25.6, 25.95),
    lat_col="latitude",
    lon_col="longitude"
)
```

### Run with MPI Parallelization

For larger simulations, use multiple processors:

```bash
# Run with 4 processors
mpiexec -n 4 python gebco_simulation.py
```

Or in Python:

```python
solver = physrag.solver.SWESolver(config=config)

# Check MPI settings
print(f"Running on {solver.size} processors")
print(f"This processor is rank {solver.rank}")

# Only rank 0 does I/O
if solver.rank == 0:
    print("Output will be saved from this process")
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'physrag'"

The package isn't installed or environment isn't activated:

```bash
# Activate environment
conda activate physrag-swe

# Verify installation
python -c "import physrag; print(physrag.__file__)"

# If not in environment, reinstall
pip install -e /path/to/physrag-swe
```

### "ModuleNotFoundError: No module named 'clawpack'"

PyClaw isn't installed:

```bash
conda activate physrag-swe
conda install -c conda-forge clawpack
```

### "ImportError: cannot import name 'PyClaw'"

Old version of PyClaw. Update it:

```bash
conda activate physrag-swe
conda update -c conda-forge clawpack
```

### "Simulation unstable (NaN output)"

CFL condition violated. Reduce time step:

```python
config = physrag.config.SimulationConfig(
    # ... other parameters
    dt=0.5,  # Smaller time step
    cfl_desired=0.8,  # More conservative
)
```

### "GEBCO download fails"

Check internet connection and server availability:

```python
import physrag

# Try downloading GEBCO bathymetry
try:
    df = physrag.bathymetry_retrieval.download_gebco_ascii(
        extent=extent
    )
except Exception as e:
    print(f"Download failed: {e}")
    print("Download manually from https://www.gebco.net/")
```

---

## Next Steps

1. **Run the examples** — Try `simple_simulation.py`, `gebco_simulation.py`, and `data_integration_simulation.py`

2. **Read the documentation**
   - [Architecture Overview](./architecture.md) — Design & concepts
   - [API Reference](./classes/data_providers.md) — Detailed API docs
   - [Bathymetry Guide](./classes/bathymetry.md) — GEBCO usage
   - [Interpolation Guide](./classes/data_interpolation.md) — Data integration

3. **Explore example scripts** — See `examples/` folder for more complete examples

4. **Check results**
   - Solutions saved to `output_*/`
   - Read with `physrag.utils.read_solutions()`
   - Visualize with `physrag.utils.animate_solution()`

5. **Customize for your domain**
   - Adjust `lon_range`, `lat_range` for your region
   - Load proper GEBCO bathymetry
   - Integrate your observation data
   - Add wind forcing for storms

---

## Help & Support

- **Questions?** Open an [issue on GitHub](https://github.com/yourrepo/physrag-swe/issues)
- **Found a bug?** [Report it](https://github.com/yourrepo/physrag-swe/issues/new)
- **Contributing?** See [Contributing Guide](../CONTRIBUTING.md)

---

