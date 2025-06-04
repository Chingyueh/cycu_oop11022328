# -*- coding: utf-8 -*-
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine

def visualize_bus_route(route_id: str, shapefile_path: str, db_path: str):
    # 1. 讀取村里界 Shapefile
    village_shp = gpd.read_file(shapefile_path)

    # 2. 過濾北北基桃
    target_cities = ['臺北市', '新北市', '基隆市', '桃園市']
    filtered_village_shp = village_shp[village_shp['COUNTYNAME'].isin(target_cities)]

    # 3. 從 SQLite 讀取公車站點
    engine = create_engine(f"sqlite:///{db_path}")
    query = f"""
        SELECT stop_name, latitude, longitude
        FROM data_route_info_busstop
        WHERE route_id = '{route_id}'
    """
    bus_stops = pd.read_sql(query, engine)

    if bus_stops.empty:
        print(f"❌ 查無路線 {route_id} 的站點資訊，請確認是否已爬取儲存")
        return

    # 4. 轉換經緯度為 float
    bus_stops['latitude'] = bus_stops['latitude'].astype(float)
    bus_stops['longitude'] = bus_stops['longitude'].astype(float)

    # 5. 畫圖
    fig, ax = plt.subplots(figsize=(12, 10))
    filtered_village_shp.plot(ax=ax, color='lightblue', edgecolor='black', label='村里界')

    # 畫出公車站點
    ax.plot(bus_stops['longitude'], bus_stops['latitude'], color='red', marker='o', linestyle='-', linewidth=2, label='Bus Route')

    # 標註站名
    for idx, row in bus_stops.iterrows():
        ax.annotate(row['stop_name'], (row['longitude'], row['latitude']), fontsize=8, color='darkred')

    ax.set_title(f'Route {route_id} 公車路線圖', fontsize=16)
    plt.tight_layout()
    plt.legend()
    plt.savefig(f'bus_route_map_{route_id}.png', dpi=300)
    plt.show()

if __name__ == "__main__":
    route_id = input("請輸入要視覺化的公車 route_id：")
    shapefile_path = '20250520/\u6751(\u91cc)\u754c(TWD97\u7d93\u7def\u5ea6)1140318/VILLAGE_NLSC_1140318.shp'
    db_path = 'data/hermes_ebus_taipei.sqlite3'
    visualize_bus_route(route_id, shapefile_path, db_path)
