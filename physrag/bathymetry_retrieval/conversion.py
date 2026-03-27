"""
GEBCO data conversion module.

Parses GEBCO OPeNDAP ASCII responses into pandas DataFrames.
Optionally saves to CSV for persistence.
"""

import re
from pathlib import Path

import pandas as pd


def parse_gebco_ascii(
    txt_filepath, save_csv=False, output_csv_path=None
) -> pd.DataFrame:
    """
    Parse GEBCO OPeNDAP ASCII response into a pandas DataFrame.

    Reads raw OPeNDAP ASCII format data and converts it into a tabular DataFrame
    with Longitude, Latitude, and Elevation columns. Optionally exports to CSV.

    OPeNDAP ASCII format structure:
        - DDS header describing dimensions
        - Data separator line (-----)
        - lon[n] array values (on next line(s))
        - lat[m] array values (on next line(s))
        - crs value (coordinate reference system)
        - elevation.elevation[m][n] grid (m rows × n columns)
        - elevation.lat[m] and elevation.lon[n] coordinate arrays (duplicates)

    Args:
        txt_filepath (str): Path to the downloaded OPeNDAP ASCII text file.
        save_csv (bool): If True, also save DataFrame to CSV file.
            Defaults to False (in-memory only).
        output_csv_path (str): Output CSV path. If None and save_csv=True,
            uses same base name as txt_filepath with .csv extension.

    Returns:
        pandas.DataFrame: Flattened grid data with columns [Longitude, Latitude, Elevation].
            Each row represents one grid point.
    """
    # Read the entire ASCII file into memory
    with open(txt_filepath, "r") as f:
        content = f.read()
    lines = content.split("\n")

    # Initialize storage for parsed data
    lons = []  # Longitude coordinate array
    lats = []  # Latitude coordinate array
    elevations = []  # 2D elevation grid (list of rows)
    current_section = None  # Track which section we're parsing
    i = 0  # Line index for manual iteration

    while i < len(lines):
        line = lines[i].strip()
        i += 1

        # Skip empty lines and headers
        if not line or line.startswith("Dataset") or line.startswith("bodc"):
            continue

        # Separator line
        if "-----" in line:
            continue

        # Parse lon array (dimension header followed by values on next line(s))
        if line.startswith("lon["):
            # Accumulate all value lines until we hit the next section
            values_lines = []
            while i < len(lines):
                next_line = lines[i].strip()
                # Stop at section boundaries
                if (
                    not next_line
                    or next_line.startswith("lat[")
                    or next_line.startswith("crs")
                ):
                    break
                if next_line.startswith("elevation") or "-----" in next_line:
                    break
                values_lines.append(next_line)
                i += 1

            # Join and parse comma-separated values as floats
            values_str = ", ".join(values_lines)
            lons = [float(x.strip()) for x in values_str.split(",") if x.strip()]
            continue

        # Parse lat array (dimension header followed by values on next line(s))
        if line.startswith("lat["):
            # Accumulate all value lines until we hit the next section
            values_lines = []
            while i < len(lines):
                next_line = lines[i].strip()
                # Stop at section boundaries
                if not next_line or next_line.startswith("crs"):
                    break
                if next_line.startswith("elevation") or "-----" in next_line:
                    break
                values_lines.append(next_line)
                i += 1

            # Join and parse comma-separated values as floats
            values_str = ", ".join(values_lines)
            lats = [float(x.strip()) for x in values_str.split(",") if x.strip()]
            continue

        # Skip crs line
        if line.startswith("crs,"):
            current_section = None
            continue

        # Parse elevation grid
        if line.startswith("elevation.elevation"):
            current_section = "elevation"
            continue

        # Skip elevation.lat and elevation.lon duplicate arrays
        if line.startswith("elevation.lat") or line.startswith("elevation.lon"):
            current_section = None
            continue

        # Parse elevation grid rows: [row_idx], val1, val2, val3, ...
        if current_section == "elevation" and line.startswith("["):
            # Extract row index and values using regex pattern
            match = re.search(r"\[\d+\],\s*(.*)", line)
            if match:
                values_str = match.group(1)
                # Parse comma-separated values as floats for this row
                row = [float(x.strip()) for x in values_str.split(",") if x.strip()]
                elevations.append(row)
            continue

    # Initialize DataFrame structure
    data = {"Longitude": [], "Latitude": [], "Elevation": []}

    # Flatten 2D elevation grid into 1D rows (nested iteration: lat × lon)
    for lat_idx, lat_val in enumerate(lats):
        for lon_idx, lon_val in enumerate(lons):
            # Validate grid indices before accessing to avoid out-of-bounds errors
            if lat_idx < len(elevations) and lon_idx < len(elevations[lat_idx]):
                elev_val = elevations[lat_idx][lon_idx]
                data["Longitude"].append(lon_val)
                data["Latitude"].append(lat_val)
                data["Elevation"].append(elev_val)

    # Convert dictionary to pandas DataFrame for columnar access
    df = pd.DataFrame(data)

    # Optionally save to CSV for external use
    if save_csv:
        if output_csv_path is None:
            txt_path = Path(txt_filepath)
            output_csv_path = txt_path.with_suffix(".csv")
        df.to_csv(output_csv_path, index=False)
        print(f"Saved CSV to: {output_csv_path}")

    # Provide summary of parsed data
    print(f"Parsed GEBCO data from: {txt_filepath}")
    print(f"  Longitudes: {len(lons)} values from {lons[0]:.4f}° to {lons[-1]:.4f}°")
    print(f"  Latitudes: {len(lats)} values from {lats[0]:.4f}° to {lats[-1]:.4f}°")
    print(
        f"  Elevation grid: {len(elevations)} rows × {len(elevations[0]) if elevations else 0} columns"
    )
    print(f"  Total records: {len(df)}")

    return df
