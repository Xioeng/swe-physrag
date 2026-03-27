import pandas as pd

from physrag import rag_data_retrieval


def aggregate_data_by_location(
    df: pd.DataFrame, lon_col: str, lat_col: str, value_col: str
) -> pd.DataFrame:
    """Aggregate weather data by location, averaging values at duplicate coordinates."""
    return (
        df.groupby([lon_col, lat_col], as_index=False)
        .agg({value_col: "mean"})
        .reset_index(drop=True)
    )


def load_data_and_aggregate_by_location(
    csv_path: str,
    extent: tuple,
    lon_lat_col_names: tuple,
    values_col_name: str,
    timestamp_col: str,
) -> pd.DataFrame:
    longitude_col, latitude_col = lon_lat_col_names
    weather_df = rag_data_retrieval.read_csv_extent(
        csv_path=csv_path,
        extent=extent,
        lat_col=latitude_col,
        lon_col=longitude_col,
        columns=[longitude_col, latitude_col, values_col_name],
        timestamp_col=timestamp_col,
    )
    weather_df = aggregate_data_by_location(
        weather_df,
        lon_col=longitude_col,
        lat_col=latitude_col,
        value_col=values_col_name,
    )
    return weather_df
