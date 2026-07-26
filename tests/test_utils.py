"""
Tests for utility functions in physrag.utils module.

Tests cover geographic extent validation and other helper functions.

Run with: pytest tests/test_utils.py -v
"""

import pytest

from physrag.utils import is_valid_extent

# is_valid_extent tests


def test_valid_extent_global():
    """Test valid global extent."""
    assert is_valid_extent((-180, 180, -90, 90)) is True


def test_valid_extent_miami():
    """Test valid Miami area extent."""
    assert is_valid_extent((-80.2, -80.0, 25.6, 25.95)) is True


def test_valid_extent_florida():
    """Test valid Florida state extent."""
    assert is_valid_extent((-87.6, -80.0, 24.5, 30.8)) is True


def test_valid_extent_with_list():
    """Test that lists are accepted as well as tuples."""
    assert is_valid_extent([-80.2, -80.0, 25.6, 25.95]) is True


def test_invalid_extent_wrong_number_of_elements():
    """Test that extent with wrong number of elements raises ValueError."""
    with pytest.raises(ValueError, match="must have 4 elements"):
        is_valid_extent((-80.2, -80.0, 25.6))


def test_invalid_extent_too_many_elements():
    """Test that extent with too many elements raises ValueError."""
    with pytest.raises(ValueError, match="must have 4 elements"):
        is_valid_extent((-80.2, -80.0, 25.6, 25.95, 0))


def test_invalid_extent_south_greater_than_north():
    """Test that south > north raises ValueError."""
    with pytest.raises(ValueError, match="Invalid latitude bounds"):
        is_valid_extent((-80.2, -80.0, 30.0, 25.0))


def test_invalid_extent_north_greater_than_90():
    """Test that north > 90 raises ValueError."""
    with pytest.raises(ValueError, match="Invalid latitude bounds"):
        is_valid_extent((-80.2, -80.0, 25.0, 91.0))


def test_invalid_extent_south_less_than_minus_90():
    """Test that south < -90 raises ValueError."""
    with pytest.raises(ValueError, match="Invalid latitude bounds"):
        is_valid_extent((-80.2, -80.0, -91.0, 25.0))


def test_invalid_extent_west_greater_than_east():
    """Test that west > east raises ValueError."""
    with pytest.raises(ValueError, match="Invalid longitude bounds"):
        is_valid_extent((-80.0, -80.2, 25.0, 26.0))


def test_invalid_extent_west_less_than_minus_180():
    """Test that west < -180 raises ValueError."""
    with pytest.raises(ValueError, match="Invalid longitude bounds"):
        is_valid_extent((-181.0, -80.0, 25.0, 26.0))


def test_invalid_extent_east_greater_than_180():
    """Test that east > 180 raises ValueError."""
    with pytest.raises(ValueError, match="Invalid longitude bounds"):
        is_valid_extent((-80.0, 181.0, 25.0, 26.0))


def test_boundary_latitude_north():
    """Test northern hemisphere boundary (90°N)."""
    assert is_valid_extent((-180, 180, 0, 90)) is True


def test_boundary_latitude_south():
    """Test southern hemisphere boundary (-90°S)."""
    assert is_valid_extent((-180, 180, -90, 0)) is True


def test_boundary_longitude_dateline():
    """Test international date line boundary."""
    assert is_valid_extent((-180, 180, -45, 45)) is True


def test_equal_south_north():
    """Test with equal south and north (line, not area)."""
    assert is_valid_extent((-80.2, -80.0, 25.5, 25.5)) is True


def test_equal_west_east():
    """Test with equal west and east (line, not area)."""
    assert is_valid_extent((-80.1, -80.1, 25.0, 26.0)) is True


def test_single_point_extent():
    """Test with single point (west=east, south=north)."""
    assert is_valid_extent((-80.1, -80.1, 25.5, 25.5)) is True


def test_extent_with_floats():
    """Test that float coordinates work."""
    assert is_valid_extent((-80.456, -80.123, 25.678, 25.999)) is True


def test_extent_with_negative_coordinates():
    """Test extents in southern/western hemispheres."""
    assert is_valid_extent((-120.0, -100.0, -60.0, -30.0)) is True
