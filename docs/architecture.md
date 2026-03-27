# Architecture & Design

Design principles, package structure, and integration patterns.

## Core Principles

### 1. Dependency Inversion

physrag is structured in layers:

```
Layer 1: physrag core (independent)
         └─ No external package dependencies
         └─ Works standalone

Layer 2: physrag.integrations (adapters)
         └─ Optional modules
         └─ Bridge to external packages

Layer 3: External packages (consumers)
         └─ tidalflow, pytorch, etc.
         └─ Use physrag via imports
```

**Benefit:** Core remains lightweight and reusable; integrations are optional.

### 2. Package Independence

physrag imports external packages only in integration modules:

```python
# ✅ Core module (always works)
import numpy
import pandas
# No tidalflow, pytorch, etc.

# ✅ Integration module (optional)
try:
    import tidalflow
except ImportError:
    # Handle gracefully
```

### 3. Clear Separation of Concerns

| Component | Purpose | Dependencies |
|-----------|---------|--------------|
| bathymetry_retrieval | GEBCO data access | None (requests is ok) |
| rag_data_retrieval | CSV geospatial filtering | None |
| data_interpolation | 2D sparse interpolation | scipy only |
| integrations/* | Package adapters | External packages only |

---

## Package Structure

```
physrag/
├── __init__.py                          # Package entry point
│
├── bathymetry_retrieval/                # GEBCO data retrieval
│   ├── __init__.py
│   ├── query.py                         # Build OPeNDAP queries
│   ├── retrieval.py                     # Download via OPeNDAP
│   └── conversion.py                    # Parse to DataFrame
│
├── rag_data_retrieval/                  # CSV/geospatial filtering
│   ├── __init__.py
│   └── csv_retrieval.py                 # CSV operations
│
├── data_interpolation/                  # Sparse data interpolation
│   ├── __init__.py
│   └── sparse_interpolator.py           # RBF interpolation
│
├── integrations/                        # Optional adapters
│   ├── __init__.py
│   └── tidalflow_providers.py          # tidalflow adapters
│
└── utils.py                             # Shared utilities
```

### Module Responsibilities

**bathymetry_retrieval**
- Build OPeNDAP query strings
- Download GEBCO data
- Parse ASCII to DataFrame
- Cache management

**rag_data_retrieval**
- Load CSV files
- Filter by geographic extent (lon/lat bounds)
- Filter by temporal range (optional)
- Column mapping and selection

**data_interpolation**
- Sparse 2D point data management
- RBF-based interpolation
- Uncertainty estimation
- Efficient caching

**integrations/tidalflow_providers**
- Wrap physrag data for tidalflow interfaces
- Handle missing tidalflow gracefully
- Provide two main adapter classes:
  - `BathymetryFromGEBCO` → implements tidalflow BathymetryProvider
  - `WaterLevelInterpolationProvider` → implements tidalflow InitialConditionProvider

---

## Integration Pattern

When adding support for a new package (e.g., `my_package`):

### 1. Create Integration Module

```python
# physrag/integrations/my_package_providers.py

from typing import Tuple
import numpy as np

# Import your data modules
from physrag import bathymetry_retrieval, data_interpolation

# Try-except for optional external package
try:
    import my_package
    HAS_MY_PACKAGE = True
except ImportError:
    HAS_MY_PACKAGE = False


class MyPackageAdapter:
    """Adapts physrag data to my_package interface."""
    
    def __init__(self, physrag_data):
        if not HAS_MY_PACKAGE:
            raise ImportError(
                "my_package is required. "
                "Install with: [instructions here]"
            )
        self.data = physrag_data
    
    def to_my_package_format(self):
        """Convert physrag data to my_package format."""
        # Implement conversion
        pass
```

### 2. Export in __init__.py

```python
# physrag/integrations/__init__.py

__all__ = []  # or list specific classes you want to export
```

### 3. Update pyproject.toml (if pip-installable)

```toml
[project.optional-dependencies]
my-package = ["my-package>=1.0"]
```

Note: For packages requiring conda (like tidalflow), don't add to pyproject.toml.

---

## Data Flow Patterns

### Pattern 1: Core Data Retrieval (Standalone)
```
User Script
    ↓
physrag.bathymetry_retrieval.download_gebco_ascii()
    ↓
GEBCO OPeNDAP Server
    ↓
pandas.DataFrame
```

### Pattern 2: CSV Filtering
```
User Script
    ↓
physrag.rag_data_retrieval.read_csv_extent()
    ↓
Local CSV File
    ↓
Filtered pandas.DataFrame
```

### Pattern 3: Data Interpolation
```
Sparse Measurements
    ↓
physrag.data_interpolation.SparseDataInterpolator
    ↓
Regular Grid
    ↓
Interpolated Values + Uncertainties
```

### Pattern 4: Integration (With External Package)
```
physrag Data
    ↓
physrag.integrations.my_package_providers.Adapter
    ↓
External Package Interface
    ↓
External Package Computation
```

---

## Design Decisions

### Why Separate Files Over Monolithic Module?

✅ **Modularity:** Each subpackage has clear responsibility  
✅ **Reusability:** Users import only what they need  
✅ **Testability:** Test each module independently  
✅ **Maintainability:** Changes isolated to relevant module  

### Why Try-Except for External Packages?

✅ **Graceful Degradation:** Core works without optional dependencies  
✅ **Clear Error Messages:** User knows what to install  
✅ **Flexible Installation:** Users choose their integrations  

### Why Not Use Pip Extras for tidalflow?

Conda-only packages cannot be installed via pip extras because:
1. They depend on conda for compiled libraries (HDF5, etc.)
2. Pip cannot manage conda dependencies
3. tidalflow must be built from source in conda environment

**Solution:** Document conda setup separately; handle ImportError gracefully in code.

### Why Interpolation Over Extrapolation?

RBF interpolation is used because:
- Suitable for sparse 2D point data (typical for measurements)
- Provides uncertainty estimates
- Efficient for grid evaluation
- No assumptions about data distribution

Caveats:
- Data must be reasonably dense for good results
- Extrapolation beyond measurement extent is unreliable
- Performance degrades with very large datasets

---

## Testing Strategy

### Test Isolation

```bash
# Test core (works without external packages)
pytest tests/ -k "not integration"

# Test with integrations
pytest tests/ -k "integration"

# Full test suite (requires all optional packages)
pytest tests/
```

### Mock External Packages

```python
# Don't test tidalflow behavior in physrag tests
# Only test that adapters provide correct interface

from unittest.mock import Mock
import physrag.integrations.tidalflow_providers as providers

mock_swe = Mock()
provider = providers.BathymetryFromGEBCO(extent=(...))
# Test only physrag's responsibility: correct data format
```

---

## Future Extensibility

### Adding New Data Sources

1. Create `physrag/<new_source>/` module
2. Implement retrieval, parsing, filtering functions
3. Export via `_init__.py`
4. Document in API reference

### Adding New Integrations

1. Create `physrag/integrations/<package>_providers.py`
2. Create adapter classes wrapping physrag data
3. Try-except import external package
4. Update getting-started docs

### Adding New Interpolation Methods

1. Add methods to `SparseDataInterpolator` class
2. Keep backward compatibility
3. Update documentation and examples

---

## Performance Considerations

### Memory Usage

- Large GEBCO downloads are cached in-memory (use `keep_csv=True` for persistence)
- Interpolation creates dense grids; consider chunking for very large grids
- CSV filtering is efficient (pandas vectorized operations)

### Computational Cost

- OPeNDAP downloads depend on network/server
- RBF interpolation setup: O(n³) where n=number of measurement points
- RBF evaluation: O(n) per grid point

**Optimization tips:**
- Cache downloaded data (use `keep_csv=True`)
- Reuse interpolators for multiple grids
- Chunk large interpolation grids

---

## Dependency Graph

```
physrag (core)
├── numpy
├── pandas
├── scipy
└── requests

physrag.integrations.tidalflow_providers
├── physrag (core)
└── tidalflow [OPTIONAL, conda-only]
```

No circular dependencies; clean dependency tree.
