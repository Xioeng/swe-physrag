"""
Integration tests for PhysRAG-SWE package.

Tests multiple components working together in realistic scenarios.

Run with: pytest tests/integrations/test_integration.py -v
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
import pytest

from physrag.data_interpolation import SparseDataInterpolator
from physrag.rag_data_retrieval import load_csv, read_csv_extent
from physrag.utils import is_valid_extent


@pytest.fixture
def sample_observation_data():
    """Create sample observation data CSV."""
    with TemporaryDirectory() as tmpdir:
        # Create realistic water level observations
        data = {
            "station_name": ["Station_A", "Station_B", "Station_C", "Station_D"],
            "longitude": [-80.19, -80.13, -80.10, -80.05],
            "latitude": [25.76, 26.12, 25.80, 25.90],
            "water_level_m": [0.52, 0.75, 0.31, 0.62],
            "temperature_c": [28.5, 27.8, 28.0, 28.2],
        }
        df = pd.DataFrame(data)

        csv_path = Path(tmpdir) / "observations.csv"
        df.to_csv(csv_path, index=False)

        yield csv_path


# Data retrieval to interpolation workflow tests


def test_load_filter_interpolate_workflow(sample_observation_data):
    """Test complete workflow: load → filter → interpolate."""
    csv_path = sample_observation_data

    # Step 1: Load CSV
    df = load_csv(str(csv_path))
    assert len(df) == 4

    # Step 2: Filter by extent
    extent = (-80.2, -80.08, 25.70, 26.15)
    assert is_valid_extent(extent)
    print(f"Filtering data to extent: {extent}")
    filtered = read_csv_extent(
        str(csv_path), extent, lat_col="latitude", lon_col="longitude"
    )
    assert len(filtered) > 0

    # Step 3: Interpolate water levels onto grid
    interp = SparseDataInterpolator(
        x=filtered["longitude"].values,
        y=filtered["latitude"].values,
        values=filtered["water_level_m"].values,
    )

    # Create grid for interpolation
    x_grid = np.linspace(extent[0], extent[1], 15)
    y_grid = np.linspace(extent[2], extent[3], 15)
    x_query, y_query = np.meshgrid(x_grid, y_grid)

    # Interpolate
    interp_vals, confidence = interp.interpolate(
        x_query=x_query.flatten(), y_query=y_query.flatten(), return_confidence=True
    )

    # Verify results
    assert len(interp_vals) == 225  # 15×15 grid
    assert np.all(np.isfinite(interp_vals))
    assert np.all(confidence >= 0)
    # assert np.all(confidence <= 1)


def test_multi_station_interpolation(sample_observation_data):
    """Test interpolation with multiple measurement stations."""
    csv_path = sample_observation_data

    # Load all data
    df = load_csv(str(csv_path))

    # Create interpolator with all stations
    interp = SparseDataInterpolator(
        x=df["longitude"].values,
        y=df["latitude"].values,
        values=df["water_level_m"].values,
    )

    # Test at location between stations
    interp_val, confidence = interp.interpolate(
        x_query=np.array([-80.12]), y_query=np.array([25.95])
    )

    # Should be between min and max observed values
    min_val = df["water_level_m"].min()
    max_val = df["water_level_m"].max()

    assert min_val <= interp_val[0] <= max_val


# Bathymetry and observation integration tests


def test_bathymetry_and_initial_condition_workflow():
    """Test combining bathymetry with water level observations."""
    # Create bathymetry data
    x_bathy = np.array([-80.15, -80.10])
    y_bathy = np.array([25.80, 25.85])
    elevations = np.array([-1500.0, -1200.0])

    # Create observation data
    x_obs = np.array([-80.12, -80.08])
    y_obs = np.array([25.82, 25.88])
    water_levels = np.array([0.5, 0.3])

    # Interpolate bathymetry
    bathy_interp = SparseDataInterpolator(x=x_bathy, y=y_bathy, values=elevations)

    # Interpolate observations
    obs_interp = SparseDataInterpolator(x=x_obs, y=y_obs, values=water_levels)

    # Create grid
    x_grid = np.linspace(-80.16, -80.07, 20)
    y_grid = np.linspace(25.79, 25.89, 20)
    x_query, y_query = np.meshgrid(x_grid, y_grid)

    # Interpolate both
    bathy_grid, _ = bathy_interp.interpolate(x_query.flatten(), y_query.flatten())
    obs_grid, _ = obs_interp.interpolate(x_query.flatten(), y_query.flatten())

    # Compute water depth (elevation + water level)
    bathy_grid_2d = bathy_grid.reshape(x_query.shape)
    obs_grid_2d = obs_grid.reshape(x_query.shape)
    water_depth = bathy_grid_2d + obs_grid_2d

    # Verify properties
    assert np.all(water_depth <= 0)  # Should be negative (below sea level)
    assert np.all(water_depth >= -1600)  # Should be above deepest point


def test_spatial_consistency_checks():
    """Test that interpolated data is spatially consistent."""
    # Create data with known spatial gradient
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 1.0, 2.0])
    values = np.array([0.0, 1.0, 2.0])  # Linear gradient

    interp = SparseDataInterpolator(x=x, y=y, values=values)

    # Test at regular points
    x_test = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
    y_test = np.array([0.0, 0.5, 1.0, 1.5, 2.0])

    interp_vals, _ = interp.interpolate(x_test, y_test)

    # Values should be monotonically increasing
    assert np.all(np.diff(interp_vals) >= -0.1)  # Allow small numerical error


# Data validation workflow tests


def test_extent_validation_before_filtering():
    """Test that extent is validated before filtering."""
    with TemporaryDirectory() as tmpdir:
        # Create test CSV
        data = {
            "lon": [-80.1, -80.0],
            "lat": [25.8, 25.9],
            "value": [1.0, 2.0],
        }
        df = pd.DataFrame(data)

        csv_path = Path(tmpdir) / "test.csv"
        df.to_csv(csv_path, index=False)

        # Valid extent should work
        valid_extent = (-80.15, -79.95, 25.75, 25.95)
        result = read_csv_extent(
            str(csv_path), valid_extent, lat_col="lat", lon_col="lon"
        )
        assert len(result) > 0

        # Invalid extent should raise error
        with pytest.raises(ValueError):
            invalid_extent = (-80.15, -79.95, 25.95, 25.75)  # south > north
            read_csv_extent(str(csv_path), invalid_extent, lat_col="lat", lon_col="lon")


def test_interpolator_input_validation():
    """Test that interpolator validates inputs."""
    # Valid input
    interp = SparseDataInterpolator(
        x=np.array([0.0, 1.0]), y=np.array([0.0, 1.0]), values=np.array([1.0, 2.0])
    )
    assert interp.n_stations == 2

    # Invalid input should raise error
    with pytest.raises(ValueError):
        SparseDataInterpolator(x=np.array([]), y=np.array([]), values=np.array([]))


# Real-world scenario tests


def test_hurricane_preparation_scenario():
    """Test workflow for hurricane storm surge prediction."""
    # Scenario: Prepare for hurricane at Miami (Virginia Key)
    # 1. Define study area
    extent = (-80.2, -80.05, 25.65, 25.95)
    assert is_valid_extent(extent)

    # 2. Create mock bathymetry
    bathy_x = np.array([-80.15, -80.10, -80.08])
    bathy_y = np.array([25.75, 25.80, 25.85])
    bathy_z = np.array([-2000, -1500, -500])  # Depths

    bathy_interp = SparseDataInterpolator(x=bathy_x, y=bathy_y, values=bathy_z)

    # 3. Create mock tide gauge observations
    gauge_x = np.array([-80.19, -80.13, -80.10])
    gauge_y = np.array([25.76, 26.12, 25.80])
    gauge_z = np.array([0.5, 0.8, 0.3])  # Water level above MSL

    gauge_interp = SparseDataInterpolator(x=gauge_x, y=gauge_y, values=gauge_z)

    # 4. Create simulation grid
    x_sim = np.linspace(extent[0], extent[1], 20)
    y_sim = np.linspace(extent[2], extent[3], 20)
    x_grid, y_grid = np.meshgrid(x_sim, y_sim)

    # 5. Interpolate fields
    bathy_field, _ = bathy_interp.interpolate(x_grid.flatten(), y_grid.flatten())
    water_level_field, _ = gauge_interp.interpolate(x_grid.flatten(), y_grid.flatten())

    # 6. Compute water depth
    h = (water_level_field - bathy_field).reshape(x_grid.shape)

    # 7. Verify reasonable values
    assert np.all(h >= 0)  # Positive water depth
    assert np.all(h >= -bathy_field.reshape(x_grid.shape))  # Not deeper than basin


def test_coastal_inundation_analysis():
    """Test workflow for coastal inundation mapping."""
    # Create synthetic bathymetry (coast with shallow/deep zones)
    lons = np.linspace(-80.3, -80.0, 10)
    lats = np.linspace(25.5, 26.0, 10)

    # Simple linear bathymetry: deeper offshore
    x_coast = []
    y_coast = []
    z_coast = []

    for lon in lons:
        for lat in lats:
            distance_offshore = lon + 80.15  # Distance from coast
            depth = -2000 * distance_offshore / 0.15  # Deeper offshore

            x_coast.append(lon)
            y_coast.append(lat)
            z_coast.append(depth)

    bathy_interp = SparseDataInterpolator(
        x=np.array(x_coast), y=np.array(y_coast), values=np.array(z_coast)
    )

    # Simulate storm surge
    extent = (-80.3, -80.0, 25.5, 26.0)
    x_grid = np.linspace(extent[0], extent[1], 30)
    y_grid = np.linspace(extent[2], extent[3], 30)
    x_query, y_query = np.meshgrid(x_grid, y_grid)

    bathy_field, _ = bathy_interp.interpolate(x_query.flatten(), y_query.flatten())

    # Add storm surge
    storm_surge = 2.0  # 2 meters of surge
    water_level = bathy_field + storm_surge

    # Compute inundation (where water level > 0)
    inundated = (water_level > 0).reshape(x_query.shape)

    # Check that some areas are inundated
    assert np.sum(inundated) > 0


def test_multi_source_data_fusion():
    """Test fusing data from multiple sources."""
    # Create data from different sources

    # GEBCO bathymetry
    gebco_x = np.array([-80.12, -80.08, -80.05])
    gebco_y = np.array([25.80, 25.85, 25.90])
    gebco_z = np.array([-1500, -1200, -800])

    # NOAA tide gauge
    noaa_x = np.array([-80.19])
    noaa_y = np.array([25.76])
    noaa_z = np.array([0.5])

    # Model forecast
    fcst_x = np.array([-80.10, -80.06])
    fcst_y = np.array([25.82, 25.88])
    fcst_z = np.array([1.2, 0.8])

    # Create separate interpolators
    gebco_interp = SparseDataInterpolator(x=gebco_x, y=gebco_y, values=gebco_z)
    noaa_interp = SparseDataInterpolator(x=noaa_x, y=noaa_y, values=noaa_z)
    fcst_interp = SparseDataInterpolator(x=fcst_x, y=fcst_y, values=fcst_z)

    # Combine on common grid
    extent = (-80.2, -80.04, 25.75, 25.92)
    x_grid = np.linspace(extent[0], extent[1], 15)
    y_grid = np.linspace(extent[2], extent[3], 15)
    x_query, y_query = np.meshgrid(x_grid, y_grid)

    # Interpolate all sources
    gebco_field, _ = gebco_interp.interpolate(x_query.flatten(), y_query.flatten())
    noaa_field, _ = noaa_interp.interpolate(x_query.flatten(), y_query.flatten())
    fcst_field, _ = fcst_interp.interpolate(x_query.flatten(), y_query.flatten())

    # All should have same size
    assert len(gebco_field) == len(noaa_field) == len(fcst_field)
    assert len(gebco_field) == 225  # 15×15 grid
