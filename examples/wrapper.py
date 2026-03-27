import logging

# Core physrag modules - always available
import os
import sys

import clawpack.pyclaw as pyclaw
import numpy as np

# tidalflow - external package
import tidalflow

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import physrag

# tidalflow integration - optional
from physrag.integrations.tidalflow_providers import (
    BathymetryFromGEBCO,
    InitialConditionInterpolationProvider,
    WindProviderInterpolationProviderDummy,
)

logger = tidalflow.logging_config.setup_logging(
    logging.INFO,
    "swe_example.log",
)


def run_swe_simulation(
    location: tuple,
    offset: float,
    name: str,
    csv_weather_path: str = "data/florida_weather_datasets/2024/02/2024-02-02.csv",
    wind_direction: float = 135.0,
) -> None:
    """
    Run SWE (Shallow Water Equations) simulation for a given location.

    Parameters
    ----------
    location : tuple
        (latitude, longitude) coordinates of the location
    offset : float
        Offset for the domain boundaries in degrees
    name : str
        Name of the location (e.g., 'pensacola'). Used for output directories and logging.
    csv_weather_path : str, optional
        Path to the weather dataset CSV file. Default is Florida 2024-02-02 dataset.
    wind_direction : float, optional
        Wind direction in degrees (from which the wind is coming). Default is 135.0.
    """

    # Setup logging with location-specific filename
    local_logger = tidalflow.logging_config.setup_logging(
        logging.INFO,
        f"swe_example_{name}.log",
    )

    # Configuration
    lon_range = (location[1] - offset, location[1] + offset)
    lat_range = (location[0] - offset, location[0] + offset)
    extent = (lon_range[0], lon_range[1], lat_range[0], lat_range[1])

    # Create simulation config
    config = tidalflow.config.SimulationConfig(
        # Domain
        lon_range=lon_range,
        lat_range=lat_range,
        nx=60,
        ny=60,
        # Time
        t_final=2000.0,  # seconds
        dt=10.0,  # seconds
        # Physics
        gravity=9.81,
        # Boundary conditions
        bc_lower=(pyclaw.BC.extrap, pyclaw.BC.extrap),
        bc_upper=(pyclaw.BC.extrap, pyclaw.BC.extrap),
        # Output
        output_dir=f"output_swe_example_{name}",
        multiple_output_times=True,
    )

    # ============================================================
    # Data Providers: Using physrag integration module
    # ============================================================

    local_logger.info("Creating bathymetry provider from GEBCO...")
    bathymetry_provider = BathymetryFromGEBCO(extent=extent, keep_csv=True)

    local_logger.info("Creating initial condition provider...")
    initial_condition_provider = InitialConditionInterpolationProvider(
        extent=extent,
        csv_path=csv_weather_path,
    )

    # Create water level provider using physrag's interpolation
    local_logger.info("Creating water level interpolation provider...")
    wind_provider = WindProviderInterpolationProviderDummy(
        extent=extent,
        csv_path=csv_weather_path,
        direction=wind_direction,  # Wind direction in degrees (from which the wind is coming)
    )

    # ============================================================
    # Solve with tidalflow
    # ============================================================

    local_logger.info("Initializing SWE solver...")
    solver = tidalflow.solver.SWESolver(
        config=config,
        bathymetry_provider=bathymetry_provider,
        ic_provider=initial_condition_provider,
        wind_provider=wind_provider,
    )

    local_logger.info(f"Config:\n {config}")

    # Initialize
    local_logger.info("Initializing data from providers...")
    solver.initialize_data_from_providers()
    local_logger.info(
        f"Bathymetry: min={solver.bathymetry_array.min():.2f}m, "
        f"max={solver.bathymetry_array.max():.2f}m"
    )
    local_logger.info(
        f"Initial water depth: min={solver.initial_condition_array[0].min():.2f}m, "
        f"max={solver.initial_condition_array[0].max():.2f}m"
    )
    local_logger.info(
        f"Initial x-momentum: min={solver.initial_condition_array[1].min():.2f}kg/s, "
        f"max={solver.initial_condition_array[1].max():.2f}kg/s"
    )
    local_logger.info(
        f"Initial y-momentum: min={solver.initial_condition_array[2].min():.2f}kg/s, "
        f"max={solver.initial_condition_array[2].max():.2f}kg/s"
    )
    u_wind, v_wind = solver.wind_provider.get_wind(solver.X_coord, solver.Y_coord, 0)
    wind_speed = np.sqrt(u_wind**2 + v_wind**2)
    local_logger.info(
        # f"Wind direction: {solver.wind_provider.direction} degrees from west"
        f"Wind direction: min={np.min(wind_speed):.2f}, max={np.max(wind_speed):.2f}"
    )

    # raise
    # Run simulation
    local_logger.info("Running simulation...")
    result = solver.solve()
    assert result.solution is not None

    local_logger.info(
        f"\nSimulation complete! Solution shape (T+1, 3, nx, ny): {result.solution.shape}"
    )

    # Visualize results
    if solver.rank == 0 and solver.config.output_dir is not None:
        tidalflow.utils.visualization.animate_solution(
            output_path=solver.config.output_dir,
            frames=None,
            wave_treshold=1e-2,
            save=True,
            dark_mode=True,
            writer="ffmpeg",
            file_name=f"{name}.mp4",
            fps=25,
            max_arrow_length=0.5,
            arrow_step=3,
        )
        local_logger.info("Visualization complete!")

    local_logger.info("Example completed successfully!")


def example_pensacola() -> None:
    """Example: SWE simulation for Pensacola, FL."""

    pensacola_location = (30.4044, -87.2112)
    offset = 0.15

    run_swe_simulation(location=pensacola_location, offset=offset, name="pensacola")


def example_virginia_key() -> None:
    """Example: SWE simulation for Virginia Key, FL."""

    virginia_key_location = (25.7314, -80.1618)
    offset = 0.15

    run_swe_simulation(
        location=virginia_key_location, offset=offset, name="virginia_key"
    )


def example_naples() -> None:
    """Example: SWE simulation for Naples, FL."""

    naples_location = (26.1367, -81.7883)
    offset = 0.15

    run_swe_simulation(location=naples_location, offset=offset, name="naples")


def example_panama_city() -> None:
    """Example: SWE simulation for Panama City, FL."""

    panama_city_location = (30.149723, -85.664444)
    offset = 0.15

    run_swe_simulation(location=panama_city_location, offset=offset, name="panama_city")


def example_key_west() -> None:
    """Example: SWE simulation for Key West, FL."""

    key_west_location = (24.5557, -81.8079)
    offset = 0.15

    run_swe_simulation(location=key_west_location, offset=offset, name="key_west")


if __name__ == "__main__":
    examples = [
        example_pensacola,
        example_virginia_key,
        example_naples,
        example_panama_city,
        example_key_west,
    ]

    index = 0
    if len(sys.argv) > 1 and int(sys.argv[1]) < len(examples):
        index = int(sys.argv[1])
    examples[index]()
