# Architecture & Design

Comprehensive overview of PhysRAG-SWE's layered architecture, design principles, and data flow patterns.

---

## Core Architecture

PhysRAG-SWE follows a **layered architecture** that separates concerns and enables flexible integration:

```
┌──────────────────────────────────────────────────────────────┐
│                    User Application Layer                     │
│              (Main simulation and analysis scripts)            │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│              Simulation Configuration Layer                   │
│        (SimulationConfig, Boundary Conditions, Physics)      │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────┬───────▼────────┬──────────────────┐
│     Data       │                │                  │
│  Retrieval     │   SWE Solver   │    Wind & Other  │
│                │                │    Forcing       │
├────────────────┼────────────────┼──────────────────┤
│ • Bathymetry   │• PyClaw Roe    │ • Constant wind  │
│ • Observations │• Coordinate    │ • Time-varying   │
│ • Interpolation│  mapping       │ • Parametric     │
└────────────────┴────────────────┴──────────────────┘
         │                │               │
         ▼                ▼               ▼
    ┌─────────────────────────────────────────────┐
    │        SWEResult Container & I/O            │
    │  (Output files, metadata, visualization)    │
    └─────────────────────────────────────────────┘
```

---

## Design Principles

### 1. **Separation of Concerns**

Each module has a single, well-defined responsibility:

| Layer | Module | Responsibility |
|-------|--------|-----------------|
| Data Retrieval | `bathymetry_retrieval` | Fetch & parse GEBCO bathymetry |
| Data Retrieval | `rag_data_retrieval` | Filter observations by space/time |
| Interpolation | `data_interpolation` | Interpolate sparse data to grid |
| Simulation | `config` | Configuration management & validation |
| Simulation | `solver` | SWE solving with PyClaw |
| I/O | `utils` | File I/O, visualization, analysis |

**Benefit:** Modules are testable, maintainable, and reusable independently.

### 2. **Zero External Dependencies in Core**

Core modules depend only on standard scientific stack:

```python
# Core modules (always available)
import numpy           # Core computations
import pandas          # Data manipulation
import scipy           # Interpolation
import requests        # HTTP requests

# NOT in core (optional)
# import clawpack       # Only needed for SWE solver
# import matplotlib     # Only needed for visualization
```

**Benefit:** PhysRAG-SWE can be used for data retrieval alone without installing PyClaw.

### 3. **Physics-First Data Integration**

Data retrieval and interpolation are tightly coupled with physics:

- **Bathymetry:** Must maintain proper sign conventions (negative = depth)
- **Water Level:** Integrated into initial conditions respecting bathymetry
- **Wind Forcing:** Converted to stress terms using drag coefficient formulation
- **Uncertainty:** Tracked through interpolation to quantify confidence in simulations

### 4. **Configuration-Driven Simulations**

All parameters in single `SimulationConfig` object with automatic validation:

```python
config = SimulationConfig(...)  # All params in one place
config.validate()               # Checks domain, time, physics
config.save("config.json")      # Reproducible setup
```

**Benefit:** Reproducibility and easy parameter exploration.

### 5. **Provider Pattern for Data Sources**

Abstract data provider interfaces allow flexible plug-in sources:

```python
# Built-in providers
bathymetry = GEBCOBathymetryProvider()
water_level = InterpolatedObservationsProvider()

# Custom providers
bathymetry = DatabaseBathymetryProvider()  # User-defined
```

**Benefit:** No modification to core code needed for new data sources.

---

## Package Structure

### Core Modules

```
physrag/
├── __init__.py                      # Package exports
├── config.py                        # SimulationConfig dataclass
├── solver.py                        # SWESolver main class
├── forcing.py                       # WindForcing classes
├── coordinate_mapper.py             # Geographic↔Metric mapping
├── exceptions.py                    # Custom exceptions
│
├── bathymetry_retrieval/
│   ├── __init__.py                 # Public API
│   ├── gebco_opendap.py            # OPeNDAP access
│   ├── gebco_local.py              # NetCDF loading
│   ├── providers.py                # Provider interfaces
│   └── utils.py                    # Helper functions
│
├── rag_data_retrieval/
│   ├── __init__.py
│   ├── csv_loader.py               # CSV I/O
│   ├── filters.py                  # Geographic/temporal filters
│   └── providers.py                # Provider interfaces
│
├── data_interpolation/
│   ├── __init__.py
│   ├── sparse_interpolator.py      # Main interpolation class
│   ├── rbf.py                      # RBF methods
│   ├── kriging.py                  # Kriging methods
│   └── utils.py                    # Utilities
│
├── integrations/
│   ├── __init__.py
│   └── [future integrations]       # External package adapters
│
└── utils/
    ├── __init__.py
    ├── io.py                       # File I/O
    ├── visualization.py            # Plotting
    ├── analysis.py                 # Result analysis
    └── bathymetry.py              # Bathymetry utilities
```

### Module Responsibilities

#### `config.py`

```python
class SimulationConfig:
    """Central configuration repository."""
    
    # Domain parameters
    lon_range: Tuple[float, float]      # Geographic extent
    lat_range: Tuple[float, float]
    nx: int                             # Grid resolution
    ny: int
    
    # Time stepping
    t_final: float                      # Simulation duration
    dt: float                           # Time step
    
    # Physics
    gravity: float                      # Gravitational acceleration
    
    # Boundary conditions
    bc_lower: Tuple[int, int]          # Wall/open/periodic
    bc_upper: Tuple[int, int]
    
    # Output management
    output_dir: str
    multiple_output_times: bool
    frame_interval: int
    
    # Numerical parameters
    cfl_desired: float
    cfl_max: float
```

#### `solver.py`

```python
class SWESolver:
    """Integrates PyClaw with SWE physics and data."""
    
    def __init__(self, config):
        self.config = config            # Configuration
        self.mapper = CoordinateMapper() # Geographic↔Metric
        
    def set_bathymetry(self, bathymetry: np.ndarray):
        """Set ocean floor elevation."""
        
    def set_initial_condition(self, h_hu_hv: np.ndarray):
        """Set water depth and momentum at t=0."""
        
    def set_constant_wind_forcing(self, u_wind, v_wind):
        """Set uniform wind forcing."""
        
    def setup_solver(self):
        """Initialize PyClaw structures."""
        
    def solve(self):
        """Run simulation and return solutions."""
```

#### `bathymetry_retrieval/`

**Responsibilities:**
- Query GEBCO OPeNDAP server
- Interpolate to simulation grid
- Cache data locally
- Handle missing values

**Key Functions:**
```python
fetch_gebco_opendap(extent, ...)           # Download
load_gebco_netcdf(nc_path, ...)           # Local file
interpolate_gebco_on_grid(X, Y, ...)      # To grid
```

#### `rag_data_retrieval/`

**Responsibilities:**
- Load CSV observation files
- Filter by geographic extent
- Filter by temporal range
- Map column names

**Key Functions:**
```python
read_csv_extent(csv_path, extent, ...)    # Filter CSV
read_csv_time(csv_path, time_range, ...)  # Temporal filter
```

#### `data_interpolation/`

**Responsibilities:**
- Store sparse point data
- Interpolate to grid
- Estimate uncertainty
- Cache fitted models

**Key Class:**
```python
class SparseDataInterpolator:
    def __init__(self, x, y, values, method='rbf'):
        pass
    
    def interpolate(self, x_grid, y_grid):
        return gridded_values, uncertainty
```

---

## Data Flow Patterns

### Pattern 1: Simple Slope Test (No Data)

```
┌──────────────────┐
│ SimulationConfig │────────┐
└──────────────────┘        │
                            ▼
              ┌─────────────────────┐
              │   SWESolver (init)  │
              │ • Create grid       │
              │ • Allocate arrays   │
              └─────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
  ┌──────────┐  ┌────────────┐  ┌──────────┐
  │Flat/Slope│  │ Gaussian   │  │ Wind     │
  │Bathymetry│  │ Hump       │  │ Forcing  │
  │(Analytic)│  │ (Analytic) │  │ (Formula)│
  └──────────┘  └────────────┘  └──────────┘
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              ┌─────────────────────┐
              │  solver.setup()     │
              │  solver.solve()     │
              └─────────────────────┘
                       │
                       ▼
              ┌─────────────────────┐
              │   Solutions Arrays  │
              │ (h, hu, hv at times)│
              └─────────────────────┘
```

### Pattern 2: Data-Driven (With GEBCO)

```
┌──────────────────┐
│GEBCO OPeNDAP/    │
│Local NetCDF      │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────┐
│ bathymetry_retrieval.load()     │
│ → DataFrame or numpy array      │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Interpolate to Grid             │
│ (scipy.interpolate.griddata)    │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ SimulationConfig + Bathymetry   │
│ → SWESolver.set_bathymetry()    │
└────────┬────────────────────────┘
         │
         ▼
    [Continue as Pattern 1]
```

### Pattern 3: Observations Integration

```
┌──────────────────────┐
│ Observation CSV      │
│ (Tide gauges, buoys) │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ rag_data_retrieval.read_csv_()   │
│ Filter by extent, time           │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ data_interpolation.interpolate() │
│ RBF or Kriging → Grid values     │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ Create Initial Condition         │
│ initial = [h_obs, 0, 0]         │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ SWESolver.set_initial_condition()│
└────────┬─────────────────────────┘
         │
         ▼
    [Continue as Pattern 1]
```

---

## Integration Points

### With PyClaw

SWE Solver is **thin wrapper around PyClaw**:

- PyClaw handles finite volume discretization
- PhysRAG-SWE adds bathymetry & coordinate mapping
- Wind forcing integrated via source terms

```python
# Inside SWESolver
self.claw = pyclaw.Controller()
self.claw.solver = pyclaw.ShallowWaterSolver()
self.claw.solver.bathymetry_source = self.bathymetry
self.claw.solver.wind_forcing_fn = self.wind_forcing_source_term
```

### With External Packages

Design allows for future integrations without modifying core:

```python
# Example: Integration with data assimilation framework
from physrag.integrations import DataAssimilationAdapter

da_adapter = DataAssimilationAdapter(
    solver=solver,
    observations=obs_data,
    method='ensemble_kalman_filter'
)
result = da_adapter.run()
```

---

## Error Handling & Validation

### Configuration Validation

```python
config = SimulationConfig(...)

# Automatic validation in __post_init__
# Checks:
# • Domain bounds: lon_min < lon_max, lat_min < lat_max
# • Grid: nx, ny > 0
# • Time: 0 < dt < t_final
# • Physics: gravity > 0
# • Boundary conditions: valid values (0, 1, 2)
# • CFL: 0 < cfl_desired <= cfl_max
```

### Data Validation

```python
# Bathymetry checking
assert bathymetry.shape == (ny, nx)
assert np.all(np.isfinite(bathymetry)) or np.any(np.isnan(bathymetry))

# Initial condition checking
assert h.shape == (ny, nx)
assert np.all(h >= 0)  # No negative water depths
assert np.all(np.isfinite(h))  # No NaN values allowed
```

### Exception Hierarchy

```python
class PhysRAGError(Exception):
    """Base exception for all PhysRAG errors."""

class ConfigurationError(PhysRAGError):
    """Invalid configuration parameters."""

class DataRetrievalError(PhysRAGError):
    """Failed to retrieve data."""

class InterpolationError(PhysRAGError):
    """Interpolation failed (invalid data, etc.)."""

class SolverError(PhysRAGError):
    """SWE solver encountered error."""
```

---

## Testing Architecture

### Unit Tests

Test individual modules in isolation:

```
tests/
├── test_config.py              # Configuration validation
├── test_bathymetry_retrieval/  # Data retrieval
├── test_rag_data_retrieval/    # CSV filtering
├── test_data_interpolation/    # Interpolation methods
└── test_solver/                # SWE solver
```

### Integration Tests

Test module interactions:

```
tests/integration/
├── test_retrieval_to_grid/     # Download→Interpolate
├── test_complete_workflow/     # Full simulation
└── test_mpi_simulation/        # Parallel execution
```

### Verification Tests

Test against analytical solutions:

```python
# Gaussian hump on periodic domain - known analytical solution
# Flat bathymetry dam break - self-similar solution
# Radial dam break - comparison with published results
```

---

## Performance Characteristics

### Memory Usage

| Operation | Memory |
|-----------|--------|
| SimulationConfig | ~1 KB |
| Grid (nx=100, ny=100) | ~3 MB |
| Solutions (100 time steps) | ~300 MB |
| Interpolator (1000 points) | ~10 MB |

### Computational Time

| Operation | Time (Typical) |
|-----------|----------------|
| GEBCO download | 5-30 seconds |
| Grid interpolation | 0.1-1 seconds |
| RBF interpolation setup | 0.1-5 seconds |
| SWE solve (100 steps) | 10-60 seconds |

**Optimization:**
- Cache downloaded data
- Reuse interpolators
- Use MPI for large domains
- Reduce output frequency

---

## Future Extensibility

### Adding Data Sources

1. Create module in `bathymetry_retrieval/` or `rag_data_retrieval/`
2. Implement retrieval/filtering functions
3. Optionally implement provider interface
4. Document in API reference

### Adding Interpolation Methods

1. Add method to `SparseDataInterpolator` class
2. Maintain backward compatibility
3. Implement uncertainty estimation
4. Add unit tests

### Adding Physics

1. Extend `SimulationConfig` with new parameters
2. Modify source term functions in solver
3. Validate new parameters
4. Document in physics section

---

## References

- **Software Architecture:** Gamma et al. "Design Patterns" (1994)
- **Separation of Concerns:** Dijkstra (1974)
- **Plugin Architecture:** Parnas, D. L. (1972) "On the Criteria To Be Used in Decomposing Systems into Modules"

---

