import logging

import clawpack.pyclaw as pyclaw
import numpy as np

# tidalflow - external package
import tidalflow

# Core physrag modules - always available
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


def example_pensacola() -> None:
    """Example: SWE simulation for Pensacola, FL."""

    # Configuration
    pensacola_location = (30.4044, -87.2112)
    offset = 0.2
    lon_range = (pensacola_location[1] - offset, pensacola_location[1] + offset)
    lat_range = (pensacola_location[0] - offset, pensacola_location[0] + offset)
    extent = (lon_range[0], lon_range[1], lat_range[0], lat_range[1])

    # Create simulation config
    config = tidalflow.config.SimulationConfig(
        # Domain
        lon_range=lon_range,
        lat_range=lat_range,
        nx=50,
        ny=50,
        # Time
        t_final=500.0,  # seconds
        dt=100.0,  # seconds
        # Physics
        gravity=9.81,
        # Boundary conditions
        bc_lower=(pyclaw.BC.wall, pyclaw.BC.wall),
        bc_upper=(pyclaw.BC.wall, pyclaw.BC.wall),
        # Output
        output_dir="output_swe_example_pensacola",
        multiple_output_times=True,
    )

    # ============================================================
    # Data Providers: Using physrag integration module
    # ============================================================

    logger.info("Creating bathymetry provider from GEBCO...")
    bathymetry_provider = BathymetryFromGEBCO(extent=extent, keep_csv=True)

    logger.info("Creating initial condition provider...")
    csv_weather_path = "data/florida_weather_datasets/2024/02/2024-02-02.csv"
    initial_condition_provider = InitialConditionInterpolationProvider(
        extent=extent,
        csv_path=csv_weather_path,
    )

    # Create water level provider using physrag's interpolation
    logger.info("Creating water level interpolation provider...")
    wind_provider = WindProviderInterpolationProviderDummy(
        extent=extent,
        csv_path=csv_weather_path,
        direction=135.0,  # Wind direction in degrees (from which the wind is coming)
    )
    speed = 50.0  # Wind speed in m/s
    direction = 100  # Wind direction in degrees (from which the wind is coming)
    # wind_provider = tidalflow.providers.ConstantWind(
    #     speed * np.cos(np.radians(direction)), speed * np.sin(np.radians(direction))
    # )

    # ============================================================
    # Solve with tidalflow
    # ============================================================

    logger.info("Initializing SWE solver...")
    solver = tidalflow.solver.SWESolver(
        config=config,
        bathymetry_provider=bathymetry_provider,
        ic_provider=initial_condition_provider,
        wind_provider=wind_provider,
    )

    logger.info(f"Config:\n {config}")

    # Initialize
    logger.info("Initializing data from providers...")
    solver.initialize_data_from_providers()
    logger.info(
        f"Bathymetry: min={solver.bathymetry_array.min():.2f}m, "
        f"max={solver.bathymetry_array.max():.2f}m"
    )
    logger.info(
        f"Initial water depth: min={solver.initial_condition_array[0].min():.2f}m, "
        f"max={solver.initial_condition_array[0].max():.2f}m"
    )
    logger.info(
        f"Initial x-momentum: min={solver.initial_condition_array[1].min():.2f}kg/s, "
        f"max={solver.initial_condition_array[1].max():.2f}kg/s"
    )
    logger.info(
        f"Initial y-momentum: min={solver.initial_condition_array[2].min():.2f}kg/s, "
        f"max={solver.initial_condition_array[2].max():.2f}kg/s"
    )
    u_wind, v_wind = solver.wind_provider.get_wind(solver.X_coord, solver.Y_coord, 0)
    wind_speed = np.sqrt(u_wind**2 + v_wind**2)
    logger.info(
        # f"Wind direction: {solver.wind_provider.direction} degrees from west"
        f"Wind direction: min={np.min(wind_speed):.2f}, max={np.max(wind_speed):.2f}"
    )

    # Run simulation
    logger.info("Running simulation...")
    result = solver.solve()
    assert result.solution is not None

    logger.info(
        f"\nSimulation complete! Solution shape (T+1, 3, nx, ny): {result.solution.shape}"
    )

    # Visualize results
    print(f"Visualizing results...{solver.config.output_dir}")
    if solver.rank == 0 and solver.config.output_dir is not None:
        tidalflow.utils.visualization.animate_solution(
            output_path=solver.config.output_dir,
            frames=None,
            wave_treshold=1e-2,
            save=False,
            dark_mode=False,
            writer="pillow",
            file_name="pensacola.gif",
            fps=25,
            max_arrow_length=0.5,
            arrow_step=2,
        )
        logger.info("Visualization complete!")

    logger.info("Example completed successfully!")


if __name__ == "__main__":
    example_pensacola()
