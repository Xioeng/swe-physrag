"""
Visual regression tests for sparse data interpolation.

These tests generate interpolated fields and verify plots can be created.
Visual outputs are saved to tests/artifacts/ for inspection.

Run with: pytest tests/test_interpolation_visual.py -v --tb=short
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest

from physrag.data_interpolation import SparseDataInterpolator


@pytest.fixture
def artifact_dir():
    """Create persistent artifacts directory for test outputs."""
    artifacts = Path(__file__).parent / "artifacts"
    artifacts.mkdir(exist_ok=True)
    return artifacts


@pytest.fixture
def weather_data():
    """Sample weather data from 2 stations."""
    return {
        "lon": np.array([-80.19, -80.13]),
        "lat": np.array([25.76, 26.12]),
        "temp": np.array([28.5, 27.8]),
        "x_range": (-80.25, -80.05),
        "y_range": (25.60, 26.25),
    }


@pytest.fixture
def bathymetry_data():
    """Sample bathymetry data from 2 points."""
    return {
        "lon": np.array([-80.15, -80.10]),
        "lat": np.array([25.80, 25.85]),
        "elev": np.array([-1500, -1200]),
        "x_range": (-80.20, -80.05),
        "y_range": (25.75, 25.95),
    }


@pytest.fixture
def single_station_data():
    """Sample data from single station."""
    return {
        "lon": np.array([-80.15]),
        "lat": np.array([25.85]),
        "precip": np.array([125.3]),
        "x_range": (-80.25, -80.05),
        "y_range": (25.70, 26.00),
    }


@pytest.fixture
def dense_stations_data():
    """Sample data from 20 stations (dense network)."""
    np.random.seed(42)
    n_stations = 20
    lon = np.random.uniform(-80.25, -80.05, n_stations)
    lat = np.random.uniform(25.60, 26.25, n_stations)
    # Simulate realistic temperature variation
    temp = 27.5 + 0.5 * np.cos(lon + 80.15) + 0.3 * np.sin(lat - 25.93)
    return {
        "lon": lon,
        "lat": lat,
        "temp": temp,
        "x_range": (-80.25, -80.05),
        "y_range": (25.60, 26.25),
    }


# Visual tests as functions


def test_weather_interpolation_plot(artifact_dir, weather_data):
    """Test temperature interpolation with 2 stations produces valid plot."""
    interp = SparseDataInterpolator(
        x=weather_data["lon"],
        y=weather_data["lat"],
        values=weather_data["temp"],
    )

    # Generate grid
    X, Y, Z = interp.create_grid(
        x_range=weather_data["x_range"],
        y_range=weather_data["y_range"],
        resolution=50,
    )

    # Verify interpolation succeeded
    assert Z.shape == (50, 50)
    assert not np.all(np.isnan(Z))
    assert Z.min() <= weather_data["temp"].min()
    assert Z.max() >= weather_data["temp"].max()

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 8))
    contour = ax.contourf(X, Y, Z, levels=20, cmap="RdYlBu_r")
    ax.contour(X, Y, Z, levels=10, colors="black", alpha=0.3, linewidths=0.5)
    ax.scatter(
        weather_data["lon"],
        weather_data["lat"],
        c=weather_data["temp"],
        cmap="RdYlBu_r",
        s=200,
        edgecolors="black",
        linewidths=2,
        zorder=5,
    )
    plt.colorbar(contour, ax=ax, label="Temperature (°C)")
    ax.set_title("Weather Temperature Interpolation (2 Stations)")
    ax.grid(alpha=0.3)

    # Save plot
    plot_path = artifact_dir / "weather_interpolation.png"
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    assert plot_path.exists()
    assert plot_path.stat().st_size > 0


def test_bathymetry_interpolation_plot(artifact_dir, bathymetry_data):
    """Test bathymetry interpolation produces valid plot."""
    interp = SparseDataInterpolator(
        x=bathymetry_data["lon"],
        y=bathymetry_data["lat"],
        values=bathymetry_data["elev"],
    )

    X, Y, Z = interp.create_grid(
        x_range=bathymetry_data["x_range"],
        y_range=bathymetry_data["y_range"],
        resolution=(30, 30),
    )

    assert Z.shape == (30, 30)
    assert not np.all(np.isnan(Z))

    fig, ax = plt.subplots(figsize=(10, 8))
    contour = ax.contourf(X, Y, Z, levels=15, cmap="ocean")
    ax.contour(X, Y, Z, levels=10, colors="white", alpha=0.3, linewidths=0.5)
    ax.scatter(
        bathymetry_data["lon"],
        bathymetry_data["lat"],
        c=bathymetry_data["elev"],
        cmap="ocean",
        s=200,
        edgecolors="red",
        linewidths=2,
        zorder=5,
    )
    plt.colorbar(contour, ax=ax, label="Elevation (m)")
    ax.set_title("Bathymetry Interpolation (2 Points)")

    plot_path = artifact_dir / "bathymetry_interpolation.png"
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    assert plot_path.exists()


def test_single_station_plot(artifact_dir, single_station_data):
    """Test single station produces uniform field."""
    interp = SparseDataInterpolator(
        x=single_station_data["lon"],
        y=single_station_data["lat"],
        values=single_station_data["precip"],
    )

    X, Y, Z = interp.create_grid(
        x_range=single_station_data["x_range"],
        y_range=single_station_data["y_range"],
        resolution=40,
    )

    # Single station should produce nearly constant field
    assert np.allclose(Z, Z[0, 0], atol=1e-10)

    fig, ax = plt.subplots(figsize=(10, 8))
    contour = ax.contourf(X, Y, Z, levels=15, cmap="Blues")
    ax.scatter(
        single_station_data["lon"],
        single_station_data["lat"],
        c=single_station_data["precip"],
        cmap="Blues",
        s=300,
        edgecolors="red",
        linewidths=2,
        zorder=5,
    )
    plt.colorbar(contour, ax=ax, label="Precipitation (mm)")
    ax.set_title("Single Station (Constant Field)")

    plot_path = artifact_dir / "single_station.png"
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    assert plot_path.exists()


@pytest.mark.parametrize("resolution", [10, 50, 200])
def test_multi_resolution_plots(artifact_dir, weather_data, resolution):
    """Test interpolation at different resolutions."""
    interp = SparseDataInterpolator(
        x=weather_data["lon"],
        y=weather_data["lat"],
        values=weather_data["temp"],
    )

    X, Y, Z = interp.create_grid(
        x_range=weather_data["x_range"],
        y_range=weather_data["y_range"],
        resolution=resolution,
    )

    assert Z.shape == (resolution, resolution)
    assert not np.all(np.isnan(Z))

    # Create minimal plot for each resolution
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.contourf(X, Y, Z, levels=15, cmap="RdYlBu_r")
    ax.scatter(weather_data["lon"], weather_data["lat"], c="black", s=100, zorder=5)
    ax.set_title(f"Resolution {resolution}x{resolution}")

    plot_path = artifact_dir / f"resolution_{resolution}x{resolution}.png"
    fig.savefig(plot_path, dpi=100)
    plt.close(fig)

    assert plot_path.exists()


def test_dense_stations_plot(artifact_dir, dense_stations_data):
    """Test interpolation with 20 stations (dense network)."""
    interp = SparseDataInterpolator(
        x=dense_stations_data["lon"],
        y=dense_stations_data["lat"],
        values=dense_stations_data["temp"],
    )

    X, Y, Z = interp.create_grid(
        x_range=dense_stations_data["x_range"],
        y_range=dense_stations_data["y_range"],
        resolution=100,
    )

    assert Z.shape == (100, 100)
    assert not np.all(np.isnan(Z))

    # Create plot with dense station network
    fig, ax = plt.subplots(figsize=(12, 9))
    contour = ax.contourf(X, Y, Z, levels=25, cmap="RdYlBu_r")
    ax.contour(X, Y, Z, levels=15, colors="black", alpha=0.2, linewidths=0.5)

    # Scatter stations with annotations
    scatter = ax.scatter(
        dense_stations_data["lon"],
        dense_stations_data["lat"],
        c=dense_stations_data["temp"],
        cmap="RdYlBu_r",
        s=300,
        edgecolors="black",
        linewidths=2,
        zorder=5,
        vmin=Z.min(),
        vmax=Z.max(),
    )

    # Add station numbers
    for i, (lon, lat) in enumerate(
        zip(dense_stations_data["lon"], dense_stations_data["lat"])
    ):
        ax.text(
            lon,
            lat,
            str(i + 1),
            fontsize=8,
            ha="center",
            va="center",
            color="white",
            fontweight="bold",
        )

    cbar = plt.colorbar(contour, ax=ax)
    cbar.set_label("Temperature (°C)", fontsize=12)
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)
    ax.set_title(
        f"Dense Network Interpolation (20 Stations)", fontsize=14, fontweight="bold"
    )
    ax.grid(alpha=0.3)

    plot_path = artifact_dir / "dense_stations_20.png"
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    assert plot_path.exists()
    assert plot_path.stat().st_size > 0
    print(f"✓ Dense station plot saved to {plot_path}")


def test_interpolation_confidence(weather_data):
    """Test that confidence distances are returned correctly."""
    interp = SparseDataInterpolator(
        x=weather_data["lon"],
        y=weather_data["lat"],
        values=weather_data["temp"],
    )

    query_lon = np.array([-80.15, -80.12])
    query_lat = np.array([25.90, 26.00])

    values, distances = interp.interpolate(query_lon, query_lat, return_confidence=True)

    assert len(values) == 2
    assert len(distances) == 2
    assert np.all(distances >= 0)  # Distances should be non-negative
    assert not np.any(np.isnan(distances))
