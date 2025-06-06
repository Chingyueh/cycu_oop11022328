# -*- coding: utf-8 -*-
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import os

# 設定中文字型與正負號顯示
plt.rcParams['font.family'] = 'Microsoft JhengHei'  # 適用於 Windows
plt.rcParams['axes.unicode_minus'] = False

def plot_bus_route_with_village(csv_path):
    if not os.path.exists(csv_path):
        print(f"錯誤：找不到指定的 CSV 檔案：{csv_path}")
        return

    # 1. 讀取村里界 Shapefile
    village_shp = gpd.read_file('20250520/村(里)界(TWD97經緯度)1140318/VILLAGE_NLSC_1140318.shp')

    # 2. 過濾北北基桃
    target_cities = ['臺北市', '新北市', '基隆市', '桃園市']
    filtered_village_shp = village_shp[village_shp['COUNTYNAME'].isin(target_cities)]

    # 3. 讀取公車站點（即時動態）
    bus_stops = pd.read_csv(csv_path)

    # 4. 轉換經緯度為 float
    bus_stops['lat'] = bus_stops['lat'].astype(float)
    bus_stops['lon'] = bus_stops['lon'].astype(float)

    # 5. 畫圖
    fig, ax = plt.subplots(figsize=(12, 10))

    filtered_village_shp.plot(ax=ax, color='lightblue', edgecolor='black', linewidth=0.2, label='村里界')

    # 用紅點標示公車站點
    ax.scatter(bus_stops['lon'], bus_stops['lat'], color='red', s=0.6, label='公車站點', zorder=5)

    # 用紅線依序連接公車站點
    ax.plot(bus_stops['lon'], bus_stops['lat'], color='red', linewidth=0.8, zorder=4)

    # 標註站名，字體放大兩倍（0.32）
    for idx, row in bus_stops.iterrows():
        ax.annotate(row['站名'], (row['lon'], row['lat']), fontsize=0.32, color='darkred')

    # 限制 y 軸最大值到 25.4
    ax.set_ylim(top=25.4)

    ax.set_title(f'70UPUP公車即時動態站點\n({os.path.basename(csv_path)})', fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.subplots_adjust(bottom=0.12)
    plt.legend()
    output_folder = './20250605/map'
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, f'realtime_route_map_{os.path.basename(csv_path).replace(".csv","")}.png')
    plt.savefig(output_path, dpi=300)
    plt.show()

    print(f"地圖已儲存：{output_path}")

if __name__ == '__main__':
    csv_file_path = input("請輸入即時動態CSV路徑（例如 ./20250605/realtime_0100000200_go.csv）： ").strip()
    plot_bus_route_with_village(csv_file_path)
