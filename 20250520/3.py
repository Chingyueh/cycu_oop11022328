# -*- coding: utf-8 -*-
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

# 讀取村里界 Shapefile
village_shp = gpd.read_file('20250520/村(里)界(TWD97經緯度)1140318/VILLAGE_NLSC_1140318.shp')

print(village_shp['COUNTYNAME'].unique())

# 過濾北北基桃
target_cities = ['臺北市', '新北市', '基隆市', '桃園市']
filtered_village_shp = village_shp[village_shp['COUNTYNAME'].isin(target_cities)]

# 繪圖
fig, ax = plt.subplots(figsize=(12, 10))
filtered_village_shp.plot(ax=ax, color='lightblue', edgecolor='black', label='村里界')
ax.set_title('Taipei, New Taipei, Keelung, Taoyuan Map (Village Boundaries)', fontsize=16)
plt.tight_layout()

# 輸出圖檔
output_file = '20250520/north_taiwan_village_map.png'
plt.savefig(output_file, dpi=300)
print(f"Map saved to {output_file}")

plt.show()