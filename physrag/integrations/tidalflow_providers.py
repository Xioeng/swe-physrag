"""
tidalflow integration providers for physrag data.

This module adapts physrag data sources to tidalflow provider interfaces.
These classes bridge the gap between physrag's data retrieval capabilities
and tidalflow's expected input formats.

**Requires:** tidalflow package to be installed separately

**Example Usage:**

    import numpy as np
    from physrag.integrations.tidalflow_providers import (
        BathymetryFromGEBCO,
        WaterLevelInterpolationProvider
    )

    # Define your domain
    extent = (-87.2312, -87.0912, 30.2044, 30.4044)

    # Create bathymetry provider
    bath_provider = BathymetryFromGEBCO(
        extent=extent,
        keep_csv=True
    )

    # Create water level provider
    weather_df = ...  # Load your data
    water_level_provider = WaterLevelInterpolationProvider(
        lon=weather_df['lon'],
        lat=weather_df['lat'],
        values=weather_df['water_level']
    )

    # Use with tidalflow
    solver = tidalflow.solver.SWESolver(
        config=config,
        bathymetry_provider=bath_provider,
        ic_provider=water_level_provider
    )
"""

import numpy as np
import numpy.typing as npt
import pandas as pd
import tidalflow

import physrag.integrations.utils
from physrag import bathymetry_retrieval, data_interpolation


class BathymetryFromGEBCO(tidalflow.providers.BathymetryProvider):
    """
    Bathymetry provider using GEBCO data for tidalflow.

    Wraps physrag.bathymetry_retrieval to provide bathymetry data
    in tidalflow's expected format.

    Args:
        extent: Tuple of (west, east, south, north) in lon/lat
        keep_csv: Whether to save downloaded data as CSV
        csv_path: Optional path to pre-downloaded CSV file
    """

    def __init__(
        self,
        extent: tuple[float, float, float, float],
        keep_csv: bool = False,
    ):
        self.extent = extent
        self.keep_csv = keep_csv
        self.csv_path: str | None = None
        self._bathymetry_data: pd.DataFrame = pd.DataFrame()
        self._interpolator: data_interpolation.SparseDataInterpolator

        # Prepare data
        self._bathymetry_data, _, self.csv_path = bathymetry_retrieval.get_gebco_data(
            extent=self.extent,
            keep_csv=self.keep_csv,
            keep_txt=False,
        )
        # Set up interpolator
        self._interpolator = data_interpolation.SparseDataInterpolator(
            x=self._bathymetry_data["Longitude"].values,
            y=self._bathymetry_data["Latitude"].values,
            values=self._bathymetry_data["Elevation"].values,
        )

    def get_bathymetry(
        self, lon_grid: npt.NDArray[np.float64], lat_grid: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.float64]:
        """
        Get bathymetry values at specified grid points.

        Args:
            lon_grid: Longitude grid points (2D array)
            lat_grid: Latitude grid points (2D array)

        Returns:
            Bathymetry elevation at grid points
        """

        # Interpolate at grid points
        bath_values, _ = self._interpolator.interpolate(
            lon_grid.flatten(), lat_grid.flatten()
        )

        return bath_values.reshape(lon_grid.shape)


class InitialConditionInterpolationProvider(
    tidalflow.providers.InitialConditionProvider
):
    """
    Water level (initial condition) provider using interpolated data.

    Wraps physrag.data_interpolation to provide water level values
    in tidalflow's expected format.

    Args:
        lon: Array of longitude coordinates
        lat: Array of latitude coordinates
        values: Array of water level values
    """

    def __init__(
        self,
        extent: tuple[float, float, float, float],
        csv_path: str,
        values_col_name: str = "water_level_m_mllw",
        lon_lat_col_names: tuple[str, str] = (
            "longitude_decimal_degrees",
            "latitude_decimal_degrees",
        ),
        timestamp_col: str = "timestamp_utc_iso8601",
    ):
        # Load data from CSV

        self.csv_path = csv_path
        self._data: pd.DataFrame
        self._interpolator: data_interpolation.SparseDataInterpolator

        self._data = physrag.integrations.utils.load_data_and_aggregate_by_location(
            csv_path=csv_path,
            extent=extent,
            lon_lat_col_names=lon_lat_col_names,
            values_col_name=values_col_name,
            timestamp_col=timestamp_col,
        )

        self._interpolator = data_interpolation.SparseDataInterpolator(
            x=self._data[lon_lat_col_names[0]],
            y=self._data[lon_lat_col_names[1]],
            values=self._data[values_col_name],
        )

    def get_initial_condition(
        self, lon_grid: npt.NDArray[np.float64], lat_grid: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.float64]:
        """
        Get initial water depth at grid points.

        Args:
            lon_grid: Longitude grid points (2D array)
            lat_grid: Latitude grid points (2D array)

        Returns:
            Shape (3, nx, ny) array with:
                [0]: water depth
                [1]: x-momentum
                [2]: y-momentum
        """
        # Interpolate at grid points
        data, _ = self._interpolator.interpolate(lon_grid.flatten(), lat_grid.flatten())

        # Return in tidalflow format: (3, nx, ny)
        initial_condition = np.zeros((3, *lon_grid.shape))
        initial_condition[0] = data.reshape(lon_grid.shape)  # Water depth
        # Momentum components (0,0) initialized to zero

        return initial_condition


class WindProviderInterpolationProviderDummy(tidalflow.providers.WindProvider):
    """
    Wind provider using interpolated data.

    Wraps physrag.data_interpolation to provide wind speed and direction
    in tidalflow's expected format.

    Args:
        lon: Array of longitude coordinates
        lat: Array of latitude coordinates
        speed_values: Array of wind speed values
        direction_values: Array of wind direction values (degrees from north)
    """

    def __init__(
        self,
        extent: tuple[float, float, float, float],
        csv_path: str,
        direction: float,
        values_col_name: str = "wind_speed_m_per_s",
        lon_lat_col_names: tuple[str, str] = (
            "longitude_decimal_degrees",
            "latitude_decimal_degrees",
        ),
        timestamp_col: str = "timestamp_utc_iso8601",
    ):
        self.direction = direction
        self._data = physrag.integrations.utils.load_data_and_aggregate_by_location(
            csv_path=csv_path,
            extent=extent,
            lon_lat_col_names=lon_lat_col_names,
            values_col_name=values_col_name,
            timestamp_col=timestamp_col,
        )

        self._speed_interpolator = data_interpolation.SparseDataInterpolator(
            x=self._data[lon_lat_col_names[0]],
            y=self._data[lon_lat_col_names[1]],
            values=self._data[values_col_name],
        )

    def get_wind(
        self,
        lon_grid: npt.NDArray[np.float64],
        lat_grid: npt.NDArray[np.float64],
        time: float,
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """
        Get wind speed and direction at grid points.

        Args:
            lon_grid: Longitude grid points (2D array)
            lat_grid: Latitude grid points (2D array)
            time: Time (seconds)

        Returns:
            Tuple of (wind_speed, wind_direction) at grid points
        """
        speed, _ = self._speed_interpolator.interpolate(
            lon_grid.flatten(), lat_grid.flatten()
        )
        speed = speed.reshape(lon_grid.shape)

        u_speed = speed * np.cos(np.radians(self.direction))
        v_speed = speed * np.sin(np.radians(self.direction))

        return (u_speed, v_speed)


# Alias for backward compatibility with documentation examples
WaterLevelInterpolationProvider = InitialConditionInterpolationProvider
