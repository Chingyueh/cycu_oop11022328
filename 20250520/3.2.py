# -*- coding: utf-8 -*-
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine

# 1. 讀取村里界 Shapefile
village_shp = gpd.read_file('20250520/村(里)界(TWD97經緯度)1140318/VILLAGE_NLSC_1140318.shp')

# 2. 過濾北北基桃
target_cities = ['臺北市', '新北市', '基隆市', '桃園市']
filtered_village_shp = village_shp[village_shp['COUNTYNAME'].isin(target_cities)]

# 3. 從 SQLite 讀取公車站點（以 route_id = '0161000900' 為例）
db_file = "data/hermes_ebus_taipei.sqlite3"
engine = create_engine(f"sqlite:///{db_file}")
query = """
    SELECT stop_name, latitude, longitude
    FROM data_route_info_busstop
    WHERE route_id = '0161000900'
"""
bus_stops = pd.read_sql(query, engine)

# 4. 轉換經緯度為 float
bus_stops['latitude'] = bus_stops['latitude'].astype(float)
bus_stops['longitude'] = bus_stops['longitude'].astype(float)

# 5. 畫圖
fig, ax = plt.subplots(figsize=(12, 10))
filtered_village_shp.plot(ax=ax, color='lightblue', edgecolor='black', label='村里界')

# 畫出公車站點
ax.scatter(bus_stops['longitude'], bus_stops['latitude'], color='red', s=30, label='Bus Stops', zorder=5)

# 標註站名
for idx, row in bus_stops.iterrows():
    ax.annotate(row['stop_name'], (row['longitude'], row['latitude']), fontsize=8, color='darkred')

ax.set_title('Taipei, New Taipei, Keelung, Taoyuan Map (Village Boundaries) with Bus Stops', fontsize=16)
plt.tight_layout()
plt.legend()
plt.savefig('20250520/north_taiwan_village_with_bus_stops.png', dpi=300)
plt.show()