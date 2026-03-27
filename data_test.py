from physrag.bathymetry_retrieval import get_gebco_data
from physrag.rag_data_retrieval import read_csv_extent

lon_min, lon_max = -80.2015, -80.0641
lat_min, lat_max = 25.6528, 25.9287
extent = (lon_min, lon_max, lat_min, lat_max)
csv_weather_path = "data/florida_weather_datasets/2024/02/2024-02-02.csv"

df_bath, txt_path, csv_path = get_gebco_data(
    extent=extent,
    keep_txt=False,
    keep_csv=True,
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

print(df_bath.head())
print(df_weather.head(20))

import matplotlib.pyplot as plt

plt.scatter(
    df_bath.iloc[:, 0], df_bath.iloc[:, 1], c=df_bath.iloc[:, 2], cmap="viridis", s=20
)
plt.scatter(
    df_weather["longitude_decimal_degrees"],
    df_weather["latitude_decimal_degrees"],
    c="red",
    marker="x",
    label="Weather Stations",
)
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.colorbar(label="Elevation")
plt.show()
