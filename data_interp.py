from physrag.bathymetry_retrieval import get_gebco_data
from physrag.data_interpolation import SparseDataInterpolator
from physrag.rag_data_retrieval import read_csv_extent

lon_min, lon_max = -80.2015, -80.0641
lat_min, lat_max = 25.6528, 25.9287
extent = (lon_min, lon_max, lat_min, lat_max)


csv_weather_path = "data/florida_weather_datasets/2024/02/2024-02-02.csv"

df_bath, txt_path, csv_path = get_gebco_data(
    extent=extent,
    keep_txt=False,
    keep_csv=False,
)


df_weather = read_csv_extent(
    csv_path=csv_weather_path,
    extent=extent,
    lat_col="latitude_decimal_degrees",
    lon_col="longitude_decimal_degrees",
    columns=[
        "station_name",
        "water_level_m_mllw",
        "wind_speed_m_per_s",
        "precipitation_rate_mm_per_h",
    ],
    timestamp_col="timestamp_utc_iso8601",
)

print(df_weather.head(20))

df_weather = (
    df_weather.groupby(
        ["latitude_decimal_degrees", "longitude_decimal_degrees"], as_index=False
    )
    .agg(
        {
            "water_level_m_mllw": "mean",
            "wind_speed_m_per_s": "mean",
            # Add other value columns as needed
        }
    )
    .reset_index(drop=True)
)

print(df_weather.head(20))

sea_level_interp = SparseDataInterpolator(
    x=df_weather["longitude_decimal_degrees"].values,
    y=df_weather["latitude_decimal_degrees"].values,
    values=df_weather["water_level_m_mllw"].values,
)

sea_wind_interp = SparseDataInterpolator(
    x=df_weather["longitude_decimal_degrees"].values,
    y=df_weather["latitude_decimal_degrees"].values,
    values=df_weather["wind_speed_m_per_s"].values,
)

xx, yy, sea_level = sea_level_interp.create_grid(
    x_range=(lon_min, lon_max),
    y_range=(lat_min, lat_max),
    resolution=100,
)
_, _, sea_wind_x = sea_wind_interp.create_grid(
    x_range=(lon_min, lon_max),
    y_range=(lat_min, lat_max),
    resolution=100,
)

_, _, sea_wind_y = sea_wind_interp.create_grid(
    x_range=(lon_min, lon_max),
    y_range=(lat_min, lat_max),
    resolution=100,
)
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(12, 5))

axes[0].scatter(
    df_bath.iloc[:, 0], df_bath.iloc[:, 1], c=df_bath.iloc[:, 2], cmap="viridis", s=20
)
axes[0].scatter(
    df_weather["longitude_decimal_degrees"],
    df_weather["latitude_decimal_degrees"],
    c="red",
    marker="x",
    label="Weather Stations",
)
axes[0].set_xlabel("Longitude")
axes[0].set_ylabel("Latitude")
axes[0].set_title("Bathymetry Data")

axes[1].contourf(xx, yy, sea_level, levels=25, cmap="RdYlBu_r")
axes[1].set_xlabel("Longitude")
axes[1].set_ylabel("Latitude")
axes[1].set_title("Interpolated Sea Level")
axes[2].quiver(xx, yy, sea_wind_x, sea_wind_y, cmap="RdYlBu_r")
axes[2].set_xlabel("Longitude")
axes[2].set_ylabel("Latitude")
axes[2].set_title("Interpolated Wind Speed")
plt.show()
