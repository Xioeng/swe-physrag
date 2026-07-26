# Data Provider Interfaces

Base provider classes and protocols for data retrieval in PhysRAG-SWE.

## Overview

Data providers are the abstract interfaces that PhysRAG-SWE uses to retrieve bathymetry, initial conditions, and wind forcing data. This modular design allows easy extension with custom data sources.

## Provider Base Class

```python
from abc import ABC, abstractmethod
import numpy as np

class DataProvider(ABC):
    """Base class for all data providers."""
    
    @abstractmethod
    def __call__(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Retrieve data at grid points.
        
        Parameters
        ----------
        x : np.ndarray
            X-coordinates (longitude or metric)
        y : np.ndarray
            Y-coordinates (latitude or metric)
            
        Returns
        -------
        np.ndarray
            Data values at requested points
        """
        pass
```

## BathymetryProvider

Interface for bathymetry data sources:

```python
class BathymetryProvider(DataProvider):
    """Provides bathymetry data at grid points."""
    
    def __call__(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Return bathymetry (elevation/depth) at coordinates.
        
        Returns
        -------
        np.ndarray
            Bathymetry values (m). Negative = depth below MSL, 
            Positive = elevation above MSL
        """
        pass
```

### Built-in Implementations

#### GEBCOBathymetryProvider

```python
from physrag.bathymetry_retrieval import GEBCOBathymetryProvider

# Local NetCDF GEBCO file
provider = GEBCOBathymetryProvider(
    nc_path="data/gebco_2025.nc"
)

# Retrieve at points
bathymetry = provider(x_grid, y_grid)
```

**Parameters:**
- `nc_path`: Path to GEBCO NetCDF file
- `method`: Interpolation method ('linear', 'cubic', 'nearest')

**Returns:**
- Bathymetry array same shape as input coordinates

#### OPeNDAPBathymetryProvider

```python
from physrag.bathymetry_retrieval import OPeNDAPBathymetryProvider

# Remote GEBCO access via OPeNDAP
provider = OPeNDAPBathymetryProvider(
    extent=(-80.2, -80.0, 25.6, 25.95),
    cache_dir="data/gebco_cache"
)

bathymetry = provider(x_grid, y_grid)
```

**Parameters:**
- `extent`: (lon_min, lon_max, lat_min, lat_max) tuple
- `cache_dir`: Directory to cache downloaded tiles
- `server`: GEBCO server URL (defaults to official)

**Returns:**
- Bathymetry array after interpolation to grid

## InitialConditionProvider

Interface for initial water surface elevation:

```python
class InitialConditionProvider(DataProvider):
    """Provides initial water depth/elevation."""
    
    def __call__(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Return initial water elevation at coordinates.
        
        Returns
        -------
        np.ndarray
            Water elevation (m above MSL)
        """
        pass
```

### Built-in Implementations

#### StaticInitialCondition

```python
from physrag.rag_data_retrieval import StaticInitialCondition

# Constant water level
provider = StaticInitialCondition(elevation=0.2)  # 20 cm above MSL
h_init = provider(x_grid, y_grid)
```

#### InitialConditionInterpolationProvider

```python
from physrag.integrations.tidalflow_providers import (
    InitialConditionInterpolationProvider,
)

provider = InitialConditionInterpolationProvider(
    extent=(-80.2, -80.0, 25.6, 25.95),
    csv_path="data/tide_observations.csv",
    values_col_name="water_level_m_mllw",
)

h_init = provider.get_initial_condition(lon_grid, lat_grid)
```

## WindProvider

Interface for wind forcing:

```python
class WindProvider(DataProvider):
    """Provides wind stress components."""
    
    def __call__(self, x: np.ndarray, y: np.ndarray) -> tuple:
        """
        Return wind velocity components.
        
        Returns
        -------
        tuple
            (u_wind, v_wind) arrays in m/s
        """
        pass
```

### Built-in Implementations

#### ConstantWind

```python
from physrag.forcing import ConstantWind

# Hurricane wind from NE at 96 mph (42.8 m/s)
provider = ConstantWind(u_wind=-30.3, v_wind=30.3)

u, v = provider(x_grid, y_grid)
```

#### TimeVaryingWind

```python
from physrag.forcing import TimeVaryingWind
import pandas as pd

# Hurricane track data
track_df = pd.read_csv("data/hurricane_track.csv")
# Columns: time, longitude, latitude, wind_speed, wind_direction

provider = TimeVaryingWind(
    track_data=track_df,
    wind_speed_col='wind_speed',
    wind_direction_col='wind_direction',
    time_col='time'
)

u, v = provider(x_grid, y_grid)
```

#### GradientWind

```python
from physrag.forcing import GradientWind

# Analytic hurricane model with center at (x0, y0)
provider = GradientWind(
    center_x=-80.1,
    center_y=25.7,
    max_wind_speed=42.8,  # m/s (96 mph)
    radius_of_max_wind=50e3,  # 50 km
    forward_speed=5.0  # m/s
)

u, v = provider(x_grid, y_grid)
```

## Custom Providers

### Creating a Custom Provider

```python
import numpy as np
from physrag.providers import DataProvider

class MyCustomBathymetryProvider(DataProvider):
    """Example custom bathymetry provider."""
    
    def __init__(self, parameters):
        self.params = parameters
    
    def __call__(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Custom logic to compute bathymetry.
        
        Could load from:
        - Database
        - Numpy arrays
        - Computational model
        - External API
        """
        # Your implementation here
        bathymetry = np.zeros_like(x)
        
        # Example: linear slope
        bathymetry = -1000 * (x + 80) / 1.0
        
        return bathymetry
```

### Integration Example

```python
config = physrag.config.SimulationConfig(
    lon_range=(-80.2, -80.0),
    lat_range=(25.6, 25.95),
    nx=40,
    ny=40,
    # ... other parameters
)

solver = physrag.solver.SWESolver(config=config)

# Use custom provider
bathymetry_provider = MyCustomBathymetryProvider(params={})
bathymetry = bathymetry_provider(solver.X_coord, solver.Y_coord)
solver.set_bathymetry(bathymetry)
```

---

## Provider Registry

PhysRAG-SWE includes a registry for discovering available providers:

```python
from physrag.providers import get_available_providers

# List all providers
providers = get_available_providers()

# Filter by type
bathymetry_providers = providers['bathymetry']
wind_providers = providers['wind']
initial_condition_providers = providers['initial_condition']

for provider_name, provider_class in bathymetry_providers.items():
    print(f"- {provider_name}: {provider_class.__doc__}")
```

---

## Error Handling

### Common Provider Errors

**DataRetrievalError**
```python
try:
    bathymetry = provider(x_grid, y_grid)
except physrag.exceptions.DataRetrievalError as e:
    print(f"Failed to retrieve data: {e}")
    # Fallback to default value
    bathymetry = np.zeros_like(x_grid)
```

**InterpolationError**
```python
try:
    provider = InterpolatedInitialCondition(...)
except physrag.exceptions.InterpolationError as e:
    print(f"Interpolation failed: {e}")
    # Check input data validity
```

---

## Best Practices

1. **Validate Input Data**
   - Check for NaN values before interpolation
   - Verify coordinate ranges
   - Test on sample grids first

2. **Handle Edge Cases**
   - Provide sensible defaults for missing data
   - Handle extrapolation gracefully
   - Document assumptions about data bounds

3. **Performance**
   - Cache expensive computations
   - Use efficient interpolation methods
   - Consider lazy loading for large datasets

4. **Testing**
   - Unit test custom providers
   - Validate against known values
   - Check numerical stability

---
