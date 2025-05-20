import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point

# Sample city coordinates (longitude, latitude)
data = {
    'City': ['Taipei', 'Taichung', 'Kaohsiung', 'Tainan', 'Hsinchu'],
    'Longitude': [121.5654, 120.6849, 120.3014, 120.2038, 120.9686],
    'Latitude': [25.0330, 24.1477, 22.6273, 22.9999, 24.8039]
}

# Create GeoDataFrame
gdf = gpd.GeoDataFrame(
    data,
    geometry=[Point(xy) for xy in zip(data['Longitude'], data['Latitude'])],
    crs="EPSG:4326"
)

# Plot
gdf.plot(marker='o', color='red', markersize=50)
plt.title("Major Cities in Taiwan")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
for x, y, label in zip(gdf['Longitude'], gdf['Latitude'], gdf['City']):
    plt.text(x + 0.05, y, label)
plt.show()
