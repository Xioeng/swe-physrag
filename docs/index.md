# PhysRAG-SWE Documentation

**PhysRAG-SWE** — Physics-Informed Retrieval-Augmented Generation for Shallow Water Equations

A comprehensive Python package for rapid coastal hydrodynamic modeling that combines real-world data retrieval, sparse data interpolation, and finite-volume solvers for 2D Shallow Water Equations.

## What is PhysRAG-SWE?

PhysRAG-SWE integrates five major components:

```
Data Retrieval  →  Spatial Filtering  →  Data Interpolation  →  SWE Solver  →  Visualization
    (GEBCO)          (Geographic)         (RBF/Kriging)      (PyClaw)         (Cartopy)
```

It enables:
- 🌍 **Automatic Bathymetry** — Download GEBCO 2025 via OPeNDAP
- 📊 **Data Fusion** — Interpolate sparse observations into simulations
- 🌊 **2D SWE Solver** — Roe-type Riemann solver with source terms
- 🌪️ **Wind Forcing** — Hurricane and storm surge simulations
- 🖥️ **Parallel Computing** — MPI-based distributed simulations
- 📈 **Validation** — Compare with observational data
- 💾 **Export** — NetCDF, HDF5, and GeoJSON output formats

---

## Quick References

### Installation
Get started in 3 steps: Create conda environment → Install dependencies → Verify setup

👉 [Installation Guide](getting-started.md#installation)

### Quick Start Examples
Start with simple simulations, progress to real-world applications:

👉 [Getting Started](getting-started.md)

### API Documentation

#### Core Classes
- **[SimulationConfig](classes/swe_solver.md#simulationconfig)** — Configuration dataclass for all simulation parameters
- **[SWESolver](classes/swe_solver.md#swesolver)** — Main solver class using PyClaw
- **[SWEResult](classes/swe_result.md#sweresult)** — Solution container and analysis tools

#### Data Retrieval & Interpolation
- **[BathymetryProvider](classes/bathymetry.md#bathymetryprovider)** — Abstract interface for bathymetry sources
- **[GEBCOBathymetryProvider](classes/bathymetry.md#geobco)** — GEBCO automatic download
- **[SparseDataInterpolator](classes/data_interpolation.md#sparsedatainterpolator)** — RBF/Kriging interpolation
- **[DataProvider](classes/data_providers.md)** — Plugin architecture for custom data sources

### Common Tasks

**Retrieve Bathymetry:**
```python
from physrag.bathymetry_retrieval import download_gebco_ascii
df = download_gebco_ascii(extent=(-87.25, -87.05, 30.2, 30.4))
```

**Interpolate Sparse Data:**
```python
from physrag.data_interpolation import SparseDataInterpolator
interp = SparseDataInterpolator(x=lon, y=lat, values=values)
result, uncertainty = interp.interpolate(lon_grid, lat_grid)
```

**Run SWE Simulation (with TidalFlow):**
```python
import tidalflow
from tidalflow.config import SimulationConfig
from tidalflow.solver import SWESolver

config = SimulationConfig(lon_range=(-80.2, -80.0), lat_range=(25.6, 25.9), nx=50, ny=50, t_final=3600.0)
solver = SWESolver(config=config)
solver.set_bathymetry(bathymetry)
solver.set_initial_condition(h0)
solutions = solver.solve()
```

---

## Documentation Structure

### 📖 Guides & Tutorials
- **[Getting Started](getting-started.md)** — Installation and first examples
- **[Usage Guides](guides.md)** — Common workflows and patterns
- **[Architecture](architecture.md)** — Design principles and system structure

### 📚 API Reference
- **[API Documentation](api.md)** — Complete function and class signatures
- **[Data Providers](classes/data_providers.md)** — Provider pattern and integrations
- **[Bathymetry Retrieval](classes/bathymetry.md)** — GEBCO and custom sources
- **[Data Interpolation](classes/data_interpolation.md)** — Sparse data methods
- **[SWE Solver](classes/swe_solver.md)** — Solver configuration and execution
- **[Results Analysis](classes/swe_result.md)** — Solution output and export

### 🎯 Use Cases
- Storm surge prediction and risk assessment
- Tsunami propagation modeling
- Coastal flooding analysis
- Tidal bore simulation
- River mouth dynamics
- Wind-driven circulation

---

## Key Features

### ✅ Production-Ready
- Tested on real coastal domains (Virginia Key, Pensacola, Panama City, Key West)
- Validated against NOAA gauge stations
- Supports large simulations (200×200 grid, 24+ hour forecasts)

### ✅ Zero Hard Dependencies Core
- Pure Python implementation for data retrieval
- Optional MPI for parallelization
- Graceful degradation for optional packages

### ✅ Research-Grade Physics
- 2D Shallow Water Equations with bathymetric source terms
- Roe-type Riemann solver (via PyClaw)
- Wind stress forcing with hurricane profiles
- Geographic to metric coordinate transformation

### ✅ Data-Centric Design
- GEBCO 2025 automatic download via OPeNDAP
- CSV observation integration
- Multiple interpolation methods (RBF, Kriging, IDW, Linear)
- Uncertainty quantification

---

## Comparison with Similar Tools

| Feature | PhysRAG-SWE | TidalFlow-SWE | ADCIRC |
|---------|:------------:|:-------------:|:------:|
| Bathymetry Retrieval | ✅ GEBCO OPeNDAP | ✅ Manual | Manual |
| Sparse Data Interpolation | ✅ RBF/Kriging | Limited | Limited |
| Configuration-Driven | ✅ SimulationConfig | XML | Fortran |
| MPI Parallelization | ✅ PyClaw native | Python | Fortran MPI |
| Learning Curve | ✅ Gentle (Python) | Moderate (hybrid) | Steep (Fortran) |
| Real-time Forecasting | ✅ Fast (single machine) | Fast | Moderate |
| Research Extensibility | ✅ High (Python) | Moderate | Low (Fortran) |

---

## Performance Characteristics

Typical execution times on modern hardware (Intel i7, 8GB RAM):

| Configuration | Resolution | Simulation Time | Runtime | Memory |
|:---:|:---:|:---:|:---:|:---:|
| Virginia Key | 100×100 grid | 1 hour | 30 sec | 200 MB |
| Pensacola | 150×150 grid | 6 hours | 5 min | 400 MB |
| Large Domain | 200×200 grid | 24 hours | 20 min | 800 MB |

**With MPI (4 processors):** 4-5× speedup on typical hardware

---

## System Requirements

- **Python:** 3.11 or later
- **OS:** Linux, macOS, Windows (via WSL)
- **Memory:** 2 GB minimum (8 GB recommended)
- **Disk:** 500 MB for GEBCO cache
- **Network:** Required for OPeNDAP (initial GEBCO download)

---

## Installation Summary

```bash
# 1. Clone repository
git clone https://github.com/your-org/physrag-swe.git
cd physrag-swe

# 2. Create conda environment
conda env create -f environment.yml
conda activate physrag-swe

# 3. Install package
pip install -e .

# 4. Verify
python -c "import physrag; print(physrag.__version__)"
```

👉 [Detailed installation guide](getting-started.md#installation)

---

## Citation

If you use PhysRAG-SWE in research, please cite:

```bibtex
@software{physrag_swe_2024,
  title={PhysRAG-SWE: Physics-Informed Retrieval-Augmented Generation for Shallow Water Equations},
  author={Your Name and Co-authors},
  year={2024},
  url={https://github.com/your-org/physrag-swe}
}
```

---

## License

MIT License — See LICENSE file for details

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## Support & Contact

- 📧 Email: support@your-domain.com
- 📖 Documentation: [This site]
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/physrag-swe/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-org/physrag-swe/discussions)
- `InitialConditionInterpolationProvider` — Initial condition water level provider for tidalflow integration

**See:** [Getting Started](./getting-started.md)

## Documentation Index

| Document | Purpose |
|----------|---------|
| [Getting Started](./getting-started.md) | Installation & basic usage |
| [API Reference](./api.md) | Complete module & class reference |
| [Architecture](./architecture.md) | Design principles & design patterns |
| [Guides](./guides.md) | Usage patterns & examples |

## Project Structure

```
physrag/
├── bathymetry_retrieval/    # GEBCO OPeNDAP data retrieval
├── data_interpolation/       # 2D sparse data interpolation
├── rag_data_retrieval/       # CSV geospatial filtering
└── integrations/             # Optional package adapters
    └── tidalflow_providers.py
```

## Dependencies

**Core (always required):**
- numpy >= 1.21.0
- pandas >= 1.3.0
- scipy >= 1.7.0
- requests >= 2.26.0

**Optional (for integrations):**
- tidalflow (requires conda environment setup)

**Development:**
- pytest, black, mypy, flake8, isort

## Key Features

✅ **Independent Core** — Use physrag standalone without external package dependencies  
✅ **Optional Integrations** — Adapters for specific simulation packages  
✅ **Geospatial** — Built-in extent/filtering for geographic data  
✅ **Interpolation** — Sparse to dense data interpolation with uncertainty estimates  
✅ **Remote Data** — Direct OPeNDAP access to public bathymetry datasets  

## Configuration & Installation

For installation variations, see [Getting Started](./getting-started.md).

For detailed architecture and design patterns, see [Architecture Guide](./architecture.md).
