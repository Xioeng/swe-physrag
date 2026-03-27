#!/usr/bin/env python
# encoding: utf-8
"""Test for SWESolver class using the radial dam break example."""

import logging

import clawpack.petclaw as pyclaw
import numpy as np
import numpy.typing as npt
import tidalflow

import physrag

logger = tidalflow.logging_config.setup_logging(
    logging.INFO,
    "swe_example.log",
)


def test_radial_dam_break() -> None:
    """Test SWESolver with radial dam break scenario."""

    # Configuration

    # Domain bounds
    pensacola_location = (30.4044, -87.2112)

    offset = 0.2
    lon_range = (pensacola_location[1] - offset, pensacola_location[1] + offset)
    lat_range = (pensacola_location[0] - offset, pensacola_location[0] + offset)
    extent = (lon_range[0], lon_range[1], lat_range[0], lat_range[1])

    # Create configuration
    config = tidalflow.config.SimulationConfig(
        # Domain
        lon_range=lon_range,
        lat_range=lat_range,
        nx=40,
        ny=40,
        # Time
        t_final=1000.0,  # seconds
        dt=1.0,  # seconds
        # Physics
        gravity=9.81,
        # Boundary conditions
        bc_lower=(pyclaw.BC.extrap, pyclaw.BC.extrap),
        bc_upper=(pyclaw.BC.extrap, pyclaw.BC.extrap),
        # Output
        output_dir="output_swe_example_pensacola",
        multiple_output_times=True,  # Will use t_final/dt
    )

    # Wind parameters (Hurricane-like conditions)
    speed_florida = 57  # mph
    u_wind = (-1 / np.sqrt(2)) * 0.44 * speed_florida  # m/s
    v_wind = (1 / np.sqrt(2)) * 0.44 * speed_florida  # m/s

    # Providers

    print("Creating data providers...")

    # Bathymetry from GEBCO
    _, _, bath_csv_path = physrag.bathymetry_retrieval.get_gebco_data(
        extent=extent, keep_csv=True, keep_txt=False
    )
    bathymetry_provider = tidalflow.providers.BathymetryFromCSV(
        csv_path=bath_csv_path,
        columns=("Longitude", "Latitude", "Elevation"),
    )

    # Initial condition: Gaussian hump centered at domain center (in geographic coords)
    # Domain center in lon/lat
    class InitialConditionFromInterpolator(
        tidalflow.providers.InitialConditionProvider
    ):
        def __init__(
            self, interpolator: physrag.data_interpolation.SparseDataInterpolator
        ):
            self.interpolator = interpolator

        def get_initial_condition(
            self,
            lon_grid: npt.NDArray[np.float64],
            lat_grid: npt.NDArray[np.float64],
        ) -> npt.NDArray[np.float64]:
            # Interpolate values at the grid points
            data, _ = self.interpolator.interpolate(
                lon_grid.flatten(), lat_grid.flatten()
            )
            data = data.reshape(lon_grid.shape)
            initial_condition = np.zeros((3, *lon_grid.shape))  # (3, nx, ny)
            initial_condition[0] = data  # Water depth
            return initial_condition

    csv_weather_path = "data/florida_weather_datasets/2024/02/2024-02-02.csv"
    df_weather = physrag.rag_data_retrieval.read_csv_extent(
        csv_path=csv_weather_path,
        extent=extent,
        lat_col="latitude_decimal_degrees",
        lon_col="longitude_decimal_degrees",
        columns=[
            "station_name",
            "water_level_m_mllw",
            "wind_speed_m_per_s",
            "precipitation_rate_mm_per_h",
        ],
        timestamp_col="timestamp_utc_iso8601",
    )

    df_weather = (
        df_weather.groupby(
            ["latitude_decimal_degrees", "longitude_decimal_degrees"], as_index=False
        )
        .agg(
            {
                "water_level_m_mllw": "mean",
                "wind_speed_m_per_s": "mean",
                # Add other value columns as needed
            }
        )
        .reset_index(drop=True)
    )
    print(df_weather.head(20))
    # raise
    sea_level_interp = physrag.data_interpolation.SparseDataInterpolator(
        x=df_weather["longitude_decimal_degrees"].values,
        y=df_weather["latitude_decimal_degrees"].values,
        values=df_weather["water_level_m_mllw"].values,
    )
    initial_condition_provider = InitialConditionFromInterpolator(sea_level_interp)

    # Solver setup

    print("Initializing SWESolver...")
    solver = tidalflow.solver.SWESolver(
        config=config,
        bathymetry_provider=bathymetry_provider,
        ic_provider=initial_condition_provider,
    )

    print(f"Config:\n {config}")

    # Initialize data from providers

    print("Initializing data from providers...")
    solver.initialize_data_from_providers()
    print(
        f"Bathymetry: min={solver.bathymetry_array.min():.2f}m, "
        f"max={solver.bathymetry_array.max():.2f}m"
    )
    print(
        f"Initial water depth: min={solver.initial_condition_array[0].min():.2f}m, "
        f"max={solver.initial_condition_array[0].max():.2f}m"
    )

    print(f"Boundary conditions: lower={config.bc_lower}, upper={config.bc_upper}")

    # Set wind forcing (direct values, not provider)

    print(f"Setting wind forcing: u={u_wind:.2f} m/s, v={v_wind:.2f} m/s")
    solver.set_constant_wind_forcing(u_wind=u_wind, v_wind=v_wind)

    # Run simulation

    print("Setting up solver...")
    solver.setup_solver()

    print("Running simulation...")
    result = solver.solve()
    assert result.solution is not None

    print(
        f"\nSimulation complete! solution tensor (T+1, 3, nx, ny): {result.solution.shape}"
    )

    # Visualize results (only on rank 0 for MPI)

    if solver.rank == 0 and solver.config.output_dir is not None:
        tidalflow.utils.visualization.animate_solution(
            output_path=solver.config.output_dir,
            frames=None,  # It means all frames
            wave_treshold=1e-2,
            save=False,
            dark_mode=True,
            writer="pillow",
            file_name="biscayne_bay.gif",
            fps=25,
        )
        print("\nVisualization complete!")

    print("\nTest completed successfully!")


if __name__ == "__main__":
    test_radial_dam_break()
