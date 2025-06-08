# -*- coding: utf-8 -*- 
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import os
from shapely.geometry import Point

# 設定中文字型與正負號顯示
plt.rcParams['font.family'] = 'Microsoft JhengHei'  # 適用於 Windows
plt.rcParams['axes.unicode_minus'] = False

def plot_map_with_arrival(bus_stops_gdf, village_gdf, ax, base_fontsize=6):
    village_gdf.plot(ax=ax, color='lightblue', edgecolor='black', linewidth=0.2, label='村里界')

    bus_stops_gdf.plot(ax=ax, color='red', markersize=10, label='公車站點', zorder=5)
    ax.plot(bus_stops_gdf.geometry.x, bus_stops_gdf.geometry.y, color='red', linewidth=1, label='公車路線', zorder=4)

    x_offset = 0.0005
    for idx, row in bus_stops_gdf.iterrows():
        text = f"{row['站名']}, {row['到站時間']}" if pd.notna(row['到站時間']) else row['站名']
        # 交錯左右標註
        if idx % 2 == 0:
            ha = 'right'
            x_text = row.geometry.x - x_offset
        else:
            ha = 'left'
            x_text = row.geometry.x + x_offset
        y_text = row.geometry.y + base_fontsize * 0.00005
        ax.annotate(text, (x_text, y_text), fontsize=base_fontsize, color='darkred', ha=ha)

    ax.legend()

def plot_map_without_arrival(bus_stops, village_gdf, ax):
    village_gdf.plot(ax=ax, color='lightblue', edgecolor='black', linewidth=0.2, label='村里界')

    # 用紅點標示公車站點（點小）
    ax.scatter(bus_stops['lon'], bus_stops['lat'], color='red', s=0.6, label='公車站點', zorder=5)
    ax.plot(bus_stops['lon'], bus_stops['lat'], color='red', linewidth=0.8, zorder=4)

    # 標註站名，字體0.32（放大兩倍的0.16*2 =0.32）
    for idx, row in bus_stops.iterrows():
        ax.annotate(row['站名'], (row['lon'], row['lat']), fontsize=0.32, color='darkred')

    ax.legend()

def plot_bus_route_with_village(csv_path):
    if not os.path.exists(csv_path):
        print(f"錯誤：找不到指定的 CSV 檔案：{csv_path}")
        return

    # 讀取村里界 Shapefile
    village_shp = gpd.read_file('20250520/村(里)界(TWD97經緯度)1140318/VILLAGE_NLSC_1140318.shp')

    # 若村里界含全台，則只取北北基桃區域
    # 若已確認資料只含大台北地區，也可省略以下三行
    target_cities = ['臺北市', '新北市', '基隆市']
    filtered_village_shp = village_shp[village_shp['COUNTYNAME'].isin(target_cities)]



    # 讀取公車站點（即時動態）
    bus_stops = pd.read_csv(csv_path)

    # 經緯度轉 float
    bus_stops['lat'] = bus_stops['lat'].astype(float)
    bus_stops['lon'] = bus_stops['lon'].astype(float)

    # GeoDataFrame (用於右圖放大版)
    geometry = [Point(xy) for xy in zip(bus_stops['lon'], bus_stops['lat'])]
    bus_stops_gdf = gpd.GeoDataFrame(bus_stops, geometry=geometry, crs='EPSG:4326')

    # 左圖用大台北範圍
    village_bounds = filtered_village_shp.total_bounds  # minx, miny, maxx, maxy
    buffer_village = 0.05
    extent_village = (village_bounds[0] - buffer_village, village_bounds[2] + buffer_village,
                      village_bounds[1] - buffer_village, village_bounds[3] + buffer_village)

    # 右圖依公車路線範圍放大縮小
    minx, miny, maxx, maxy = bus_stops_gdf.total_bounds
    buffer_small = 0.05
    extent_small = (minx - buffer_small, maxx + buffer_small, miny - buffer_small, maxy + buffer_small)

    # 畫圖
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 9))

    # 左圖 - 大台北整區域地圖
    plot_map_without_arrival(bus_stops, filtered_village_shp, ax1)
    ax1.set_title(f'熊寶公車即時動態站點\n({os.path.basename(csv_path)})', fontsize=16)
    ax1.set_xlim(extent_village[0], extent_village[1])
    ax1.set_ylim(extent_village[2], min(25.4, extent_village[3]))

    # 右圖 - 放大版，有「站名, 到站時間」交錯標註
    plot_map_with_arrival(bus_stops_gdf, filtered_village_shp, ax2, base_fontsize=6)
    ax2.set_title(f'熊寶公車即時動態站點 放大版\n({os.path.basename(csv_path)})', fontsize=16)
    ax2.set_xlim(extent_small[0], extent_small[1])
    ax2.set_ylim(extent_small[2], min(25.4, extent_small[3]))

    plt.tight_layout()
    output_folder = './20250605/map'
    os.makedirs(output_folder, exist_ok=True)

    output_path = os.path.join(output_folder, f'realtime_route_map_{os.path.basename(csv_path).replace(".csv","")}_dual.png')
    fig.savefig(output_path, dpi=300)

    print(f"兩張地圖已儲存：{output_path}")
    plt.show()

if __name__ == '__main__':
    csv_file_path = input("請輸入即時動態CSV路徑（例如 ./20250605/realtime_0100000200_go.csv）： ").strip()
    plot_bus_route_with_village(csv_file_path)
