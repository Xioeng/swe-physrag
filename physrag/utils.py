"""
Utility functions for physrag package.

Common helper functions for data retrieval, validation, and processing.
"""


def is_valid_extent(extent: tuple | list) -> bool:
    """
    Validate a geographic extent (bounding box) format and bounds.

    Checks that the extent follows the standard format (west, east, south, north)
    and that all coordinate bounds are within valid ranges.

    Args:
        extent (tuple or list): Bounding box as (west, east, south, north).
            Follows Cartopy convention for geographic extents.

    Returns:
        bool: True if extent is valid.

    Raises:
        ValueError: If extent format or coordinate bounds are invalid.

    Example:
        >>> is_valid_extent((-82.0, -80.0, 25.0, 30.0))
        True
        >>> is_valid_extent((-82.0, -80.0, 25.0, 91.0))  # north > 90
        Traceback (most recent call last):
            ...
        ValueError: Invalid latitude bounds...
    """
    # Validate extent has exactly 4 elements
    if len(extent) != 4:
        raise ValueError(
            f"Extent must have 4 elements (west, east, south, north), got {len(extent)}"
        )

    # Unpack coordinates for validation
    west, east, south, north = extent

    # Validate latitude bounds (-90 to 90)
    if not (-90 <= south <= north <= 90):
        raise ValueError(
            f"Invalid latitude bounds: south={south}, north={north}. "
            f"Must satisfy: -90 <= south <= north <= 90"
        )

    # Validate longitude bounds (-180 to 180)
    if not (-180 <= west <= east <= 180):
        raise ValueError(
            f"Invalid longitude bounds: west={west}, east={east}. "
            f"Must satisfy: -180 <= west <= east <= 180"
        )

    return True
