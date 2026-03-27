"""
Tests for sparse data interpolation (SparseDataInterpolator).

Tests cover initialization, interpolation methods, and edge cases.

Run with: pytest tests/data_interpolation/test_sparse_interpolator.py -v
"""

import numpy as np
import pytest

from physrag.data_interpolation import SparseDataInterpolator


@pytest.fixture
def simple_interpolator():
    """Simple 2-station interpolator for testing."""
    return SparseDataInterpolator(
        x=np.array([-80.15, -80.10]),
        y=np.array([25.80, 25.85]),
        values=np.array([1.5, 1.0]),
    )


# Initialization tests


def test_init_single_station():
    """Test initialization with single station."""
    interp = SparseDataInterpolator(
        x=np.array([0.0]), y=np.array([0.0]), values=np.array([1.0])
    )
    assert interp.n_stations == 1
    assert len(interp.x) == 1


def test_init_multiple_stations():
    """Test initialization with multiple stations."""
    x = np.array([-80.15, -80.10, -80.05])
    y = np.array([25.80, 25.85, 25.90])
    values = np.array([1.5, 1.2, 1.0])

    interp = SparseDataInterpolator(x=x, y=y, values=values)
    assert interp.n_stations == 3
    np.testing.assert_array_equal(interp.x, x)
    np.testing.assert_array_equal(interp.y, y)
    np.testing.assert_array_equal(interp.values, values)


def test_init_converts_to_float():
    """Test that inputs are converted to float arrays."""
    interp = SparseDataInterpolator(x=[0, 1, 2], y=[0, 1, 2], values=[1, 2, 3])
    assert interp.x.dtype == np.float64
    assert interp.y.dtype == np.float64
    assert interp.values.dtype == np.float64


def test_init_coords_stacked_correctly():
    """Test that coordinates are stacked correctly."""
    x = np.array([0.0, 1.0])
    y = np.array([2.0, 3.0])
    values = np.array([1.0, 2.0])

    interp = SparseDataInterpolator(x=x, y=y, values=values)
    expected_coords = np.array([[0.0, 2.0], [1.0, 3.0]])
    np.testing.assert_array_equal(interp.coords, expected_coords)


def test_init_empty_raises_error():
    """Test that empty arrays raise ValueError."""
    with pytest.raises(ValueError, match="At least 1 station"):
        SparseDataInterpolator(x=np.array([]), y=np.array([]), values=np.array([]))


def test_init_mismatched_lengths_raises_error():
    """Test that mismatched array lengths raise ValueError."""
    with pytest.raises(ValueError, match="must have same length"):
        SparseDataInterpolator(
            x=np.array([0.0, 1.0]),
            y=np.array([0.0, 1.0]),
            values=np.array([1.0]),  # Wrong length
        )


def test_init_mismatched_x_y_raises_error():
    """Test that mismatched x and y lengths raise ValueError."""
    with pytest.raises(ValueError, match="must have same length"):
        SparseDataInterpolator(
            x=np.array([0.0, 1.0]),
            y=np.array([0.0]),  # Wrong length
            values=np.array([1.0, 2.0]),
        )


# Interpolation tests


def test_interpolate_single_point_at_station(simple_interpolator):
    """Test interpolation at station location returns station value."""
    interp_val, confidence = simple_interpolator.interpolate(
        x_query=np.array([-80.15]), y_query=np.array([25.80])
    )
    # Value at station should be very close to station value
    assert np.isclose(interp_val[0], 1.5, atol=0.01)


def test_interpolate_returns_confidence(simple_interpolator):
    """Test that interpolate returns confidence array."""
    interp_val, confidence = simple_interpolator.interpolate(
        x_query=np.array([-80.12]), y_query=np.array([25.82]), return_confidence=True
    )
    assert isinstance(confidence, np.ndarray)
    assert len(confidence) == 1
    assert np.all(confidence >= 0)


def test_interpolate_multiple_points(simple_interpolator):
    """Test interpolation at multiple query points."""
    x_query = np.array([-80.15, -80.10, -80.125])
    y_query = np.array([25.80, 25.85, 25.825])

    interp_vals, confidence = simple_interpolator.interpolate(
        x_query=x_query, y_query=y_query
    )

    assert len(interp_vals) == 3
    assert len(confidence) == 3


def test_interpolate_grid(simple_interpolator):
    """Test interpolation on a regular grid."""
    x_grid = np.linspace(-80.2, -80.0, 10)
    y_grid = np.linspace(25.7, 25.9, 10)
    x_query, y_query = np.meshgrid(x_grid, y_grid)

    interp_vals, confidence = simple_interpolator.interpolate(
        x_query=x_query.flatten(), y_query=y_query.flatten()
    )

    assert len(interp_vals) == 100
    assert len(confidence) == 100
    assert not np.any(np.isnan(interp_vals))


def test_interpolate_extrapolation(simple_interpolator):
    """Test that extrapolation works outside convex hull."""
    # Query point far from stations (extrapolation)
    interp_val, confidence = simple_interpolator.interpolate(
        x_query=np.array([-80.5]), y_query=np.array([25.5])
    )

    # Should use nearest neighbor for extrapolation
    # Should return a value (not NaN)
    assert not np.isnan(interp_val[0])
    assert np.isfinite(interp_val[0])


def test_interpolate_bathymetry_data():
    """Test interpolation with bathymetry-like data."""
    # Bathymetry from 3 locations
    x = np.array([-80.15, -80.10, -80.05])
    y = np.array([25.80, 25.85, 25.90])
    elevations = np.array([-1500, -1200, -800])  # Negative = depth

    interp = SparseDataInterpolator(x=x, y=y, values=elevations)

    # Interpolate on grid
    x_query = np.array([-80.125, -80.075])
    y_query = np.array([25.825, 25.875])

    interp_vals, confidence = interp.interpolate(x_query=x_query, y_query=y_query)

    # Should be between min and max depth
    assert np.all(interp_vals >= -1500)
    assert np.all(interp_vals <= -800)


def test_interpolate_temperature_data():
    """Test interpolation with temperature-like data."""
    x = np.array([-80.19, -80.13])
    y = np.array([25.76, 26.12])
    temps = np.array([28.5, 27.8])

    interp = SparseDataInterpolator(x=x, y=y, values=temps)

    # Query in middle
    interp_vals, confidence = interp.interpolate(
        x_query=np.array([-80.16]), y_query=np.array([25.94])
    )

    # Should be between the two temperatures
    assert 27.8 <= interp_vals[0] <= 28.5


# Edge case tests


def test_single_station_returns_constant():
    """Test that single station returns constant value everywhere."""
    interp = SparseDataInterpolator(
        x=np.array([0.0]), y=np.array([0.0]), values=np.array([42.0])
    )

    x_query = np.array([-10, 0, 10])
    y_query = np.array([-10, 0, 10])

    interp_vals, confidence = interp.interpolate(x_query=x_query, y_query=y_query)

    # All values should be 42 (nearest neighbor to single station)
    assert np.allclose(interp_vals, 42.0, atol=0.1)


def test_negative_coordinates():
    """Test with negative coordinates."""
    interp = SparseDataInterpolator(
        x=np.array([-1.0, 1.0]),
        y=np.array([-1.0, 1.0]),
        values=np.array([0.0, 2.0]),
    )

    interp_vals, confidence = interp.interpolate(
        x_query=np.array([0.0]), y_query=np.array([0.0])
    )

    assert np.isfinite(interp_vals[0])


def test_large_value_ranges():
    """Test with large value ranges (e.g., depth in meters)."""
    x = np.array([0.0, 1.0])
    y = np.array([0.0, 1.0])
    values = np.array([-10000, -100])  # Ocean depths

    interp = SparseDataInterpolator(x=x, y=y, values=values)

    interp_vals, confidence = interp.interpolate(
        x_query=np.array([0.5]), y_query=np.array([0.5])
    )

    assert -10000 <= interp_vals[0] <= -100


def test_closely_spaced_stations():
    """Test with stations very close together."""
    interp = SparseDataInterpolator(
        x=np.array([0.0, 0.0001]),
        y=np.array([0.0, 0.0001]),
        values=np.array([1.0, 1.001]),
    )

    interp_vals, confidence = interp.interpolate(
        x_query=np.array([0.00005]), y_query=np.array([0.00005])
    )

    assert np.isfinite(interp_vals[0])


def test_collinear_stations():
    """Test with stations in a line."""
    interp = SparseDataInterpolator(
        x=np.array([0.0, 1.0, 2.0]),
        y=np.array([0.0, 1.0, 2.0]),  # Diagonal line
        values=np.array([0.0, 1.0, 2.0]),
    )

    x_query = np.array([0.5, 1.0, 1.5])
    y_query = np.array([0.5, 1.0, 1.5])

    interp_vals, confidence = interp.interpolate(x_query=x_query, y_query=y_query)

    # Should interpolate along the line
    assert len(interp_vals) == 3
    assert not np.any(np.isnan(interp_vals))
