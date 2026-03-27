"""
GEBCO query module.

Builds OPeNDAP query strings for GEBCO data subsets.

GEBCO 2025 grid specifications:
- Longitude: -180 to 180 (86400 points), resolution: 0.004166667 degrees
- Latitude: -90 to 90 (43200 points), resolution: 0.004166667 degrees
"""

from physrag.utils import is_valid_extent

# GEBCO 2025 grid parameters
LON_MIN = -180.0
LON_MAX = 180.0
LON_SIZE = 86400
LON_RESOLUTION = (LON_MAX - LON_MIN) / LON_SIZE

LAT_MIN = -90.0
LAT_MAX = 90.0
LAT_SIZE = 43200
LAT_RESOLUTION = (LAT_MAX - LAT_MIN) / LAT_SIZE

BASE_URL = "https://dap.ceda.ac.uk/thredds/dodsC/bodc/gebco/global/gebco_2025/sub_ice_topography_bathymetry/netcdf/gebco_2025_sub_ice.nc.ascii"


def coord_to_index(coord, coord_min, resolution):
    """
    Convert a geographic coordinate to a GEBCO array index.

    Args:
        coord: Coordinate value (longitude or latitude)
        coord_min: Minimum coordinate value (-180 for lon, -90 for lat)
        resolution: Grid resolution in degrees

    Returns:
        Integer index in the array
    """
    index = (coord - coord_min) / resolution
    return int(round(index))


def build_query(extent: tuple | list, stride: int = 1) -> tuple:
    """
    Build an OPeNDAP query string for GEBCO data subset.

    Args:
        extent (tuple or list): Bounding box as (west, east, south, north).
            Follows Cartopy convention for geographic extents.
        stride (int): Sampling stride; 1 = every point, 2 = every other point, etc.
            Defaults to 1.

    Returns:
        tuple: (url, description)
            - url: Full OPeNDAP query URL
            - description: Human-readable description of the query

    Raises:
        ValueError: If extent format or coordinate bounds are invalid.
    """
    # Validate and unpack extent using shared utility
    is_valid_extent(extent)
    west, east, south, north = extent

    # Convert coordinates to array indices
    west_idx = coord_to_index(west, LON_MIN, LON_RESOLUTION)
    east_idx = coord_to_index(east, LON_MIN, LON_RESOLUTION)
    south_idx = coord_to_index(south, LAT_MIN, LAT_RESOLUTION)
    north_idx = coord_to_index(north, LAT_MIN, LAT_RESOLUTION)

    # Clamp indices to valid ranges
    west_idx = max(0, min(west_idx, LON_SIZE - 1))
    east_idx = max(0, min(east_idx, LON_SIZE - 1))
    south_idx = max(0, min(south_idx, LAT_SIZE - 1))
    north_idx = max(0, min(north_idx, LAT_SIZE - 1))

    # Build OPeNDAP query: ?var[start:stride:stop]
    query = (
        f"?lon[{west_idx}:{stride}:{east_idx}],"
        f"lat[{south_idx}:{stride}:{north_idx}],"
        f"crs,"
        f"elevation[{south_idx}:{stride}:{north_idx}][{west_idx}:{stride}:{east_idx}]"
    )

    url = BASE_URL + query

    # Format description with both bounds and indices
    description = (
        f"Extent: [W={west}°, E={east}°, S={south}°, N={north}°] | "
        f"Indices: lon[{west_idx}:{stride}:{east_idx}], lat[{south_idx}:{stride}:{north_idx}]"
    )

    return url, description


if __name__ == "__main__":
    # Test example: Gulf of Mexico (west, east, south, north)
    extent = (-80.2015, -80.0641, 25.6528, 25.9287)

    url, description = build_query(extent=extent, stride=1)
    print("Query URL:")
    print(url)
    print("\nDescription:")
    print(description)
