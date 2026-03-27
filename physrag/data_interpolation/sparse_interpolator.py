"""
Sparse 2D data interpolation and extrapolation.

Handles interpolation for measurements from 1-2 monitoring stations using griddata.
Automatically handles extrapolation with nearest-neighbor method for points outside convex hull.
"""

import warnings

import numpy as np
import numpy.typing as npt
from scipy.interpolate import griddata
from scipy.spatial import distance


class SparseDataInterpolator:
    """
    Interpolator for sparse 2D measurements from few stations using griddata.

    Uses linear interpolation for robustness with very sparse data (1-2 stations).
    Handles extrapolation via nearest-neighbor for points outside convex hull.

    Attributes:
        x (ndarray): Station x-coordinates (e.g., longitude)
        y (ndarray): Station y-coordinates (e.g., latitude)
        values (ndarray): Measurement values at stations
        coords (ndarray): Stacked (x, y) coordinates
        n_stations (int): Number of measurement stations
    """

    def __init__(
        self,
        x: npt.NDArray[np.float64],
        y: npt.NDArray[np.float64],
        values: npt.NDArray[np.float64],
    ):
        """
        Initialize the interpolator with station data.

        Args:
            x (ndarray): X-coordinates of stations (e.g., longitude), shape (n_stations,)
            y (ndarray): Y-coordinates of stations (e.g., latitude), shape (n_stations,)
            values (ndarray): Measurement values at stations, shape (n_stations,)

        Raises:
            ValueError: If dimensions don't match or no stations provided.
        """
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        values = np.asarray(values, dtype=float)

        # Validate inputs
        n_stations = len(x)
        if n_stations == 0:
            raise ValueError("At least 1 station is required.")
        if not (len(y) == len(values) == n_stations):
            raise ValueError(
                f"Coordinate and value arrays must have same length. "
                f"Got x={len(x)}, y={len(y)}, values={len(values)}"
            )

        self.x = x
        self.y = y
        self.values = values
        self.coords = np.column_stack([self.x, self.y])
        self.n_stations = n_stations

    def interpolate(
        self,
        x_query: npt.NDArray[np.float64],
        y_query: npt.NDArray[np.float64],
        return_confidence: bool = False,
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """
        Interpolate values at query points across the 2D domain.

        Uses linear interpolation within convex hull, nearest-neighbor extrapolation outside.

        Args:
            x_query (ndarray): Query x-coordinates, shape (n_query,)
            y_query (ndarray): Query y-coordinates, shape (n_query,)
            return_confidence (bool): If True, also return distance to nearest station.
                                     Default: False.

        Rpeturns:
            ndarray: Interpolated values at query points, shape (n_query,)
            ndarray (optional): If return_confidence=True, distance to nearest station.

        Raises:
            ValueError: If query dimensions are invalid.
        """
        x_query = np.asarray(x_query, dtype=float).ravel()
        y_query = np.asarray(y_query, dtype=float).ravel()

        if len(x_query) != len(y_query):
            raise ValueError(
                f"Query x and y must have same length. Got {len(x_query)} and {len(y_query)}"
            )

        coords_query = np.column_stack([x_query, y_query])

        # First pass: linear interpolation (fills convex hull)
        try:
            result = np.asarray(
                griddata(self.coords, self.values, coords_query, method="linear")
            )
        except Exception as e:
            warnings.warn(
                f"Linear interpolation failed: {e}. Falling back to nearest-neighbor."
            )
            result = np.full(
                len(coords_query), np.nan
            )  # Initialize with NaN for all points

        # Second pass: nearest-neighbor for points outside convex hull (NaN values)
        nan_mask = np.isnan(result)
        if np.any(nan_mask):
            result[nan_mask] = np.asarray(
                griddata(
                    self.coords, self.values, coords_query[nan_mask], method="nearest"
                )
            )

        if return_confidence:
            distances = self._nearest_distances(coords_query)
            return result, distances

        uncertainty = np.full(len(coords_query), np.nan)
        return result, uncertainty

    def _nearest_distances(
        self, coords_query: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.float64]:
        """Compute distance to nearest station for each query point.

        For geographic coordinates (lon, lat), uses Haversine distance.
        """
        # Haversine distance returns distances in radians; multiply by Earth's radius for km
        distances = distance.cdist(coords_query, self.coords, metric="euclidean")
        # (n_query, n_stations)

        # Convert from radians to kilometers (Earth radius ≈ 6371 km)
        distances_km = distances * 1111  # 1 degree ≈ 111.1 km at the equator

        nearest_distances = np.min(distances_km, axis=1)
        return nearest_distances

    def create_grid(
        self,
        x_range: tuple[float, float],
        y_range: tuple[float, float],
        resolution: tuple[int, int] | float = 100,
    ) -> tuple[
        npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.float64]
    ]:
        """
        Create a regular grid and interpolate over domain.

        Useful for visualization and SWE model input preparation.

        Args:
            x_range (tuple): (min_x, max_x) domain bounds
            y_range (tuple): (min_y, max_y) domain bounds
            resolution (int or tuple): Grid resolution. If int, creates resolution x resolution
                                      grid. If tuple, (n_x, n_y). Default: 100.

        Returns:
            X (ndarray): X mesh grid coordinates
            Y (ndarray): Y mesh grid coordinates
            Z (ndarray): Interpolated values on mesh grid
        """
        if isinstance(resolution, (int, float)):
            n_x = n_y = int(resolution)
        else:
            n_x, n_y = resolution

        x_lin = np.linspace(x_range[0], x_range[1], n_x)
        y_lin = np.linspace(y_range[0], y_range[1], n_y)
        X, Y = np.meshgrid(x_lin, y_lin)

        zz, _ = self.interpolate(X.ravel(), Y.ravel())

        Z = zz.reshape(X.shape)

        return X, Y, Z

    def summary(self) -> str:
        """Return a string summary of interpolator configuration."""
        summary_str = (
            f"SparseDataInterpolator\n"
            f"  Stations: {self.n_stations}\n"
            # f"  Method: {self.method.value}\n"
            f"  Coordinates:\n"
        )
        for i in range(self.n_stations):
            summary_str += (
                f"    Station {i + 1}: ({self.x[i]:.6f}, {self.y[i]:.6f}) "
                f"=> {self.values[i]:.4f}\n"
            )
        return summary_str
