import pandas as pd
import geopandas as gpd
import folium
from shapely.geometry import Point

# 讀取CSV檔案，這裡假設你已經擁有兩個 CSV 檔案 (去程和回程)
go_df = pd.read_csv('bus_stops_0100000A01_go.csv', encoding='utf-8-sig')
back_df = pd.read_csv('bus_stops_0100000A01_back.csv', encoding='utf-8-sig')

# 讀取 geojson 檔案，假設 'bus_stop2.geojson' 是你的檔案
geojson_path = '20250422/bus_stop2.geojson'

gdf = gpd.read_file(geojson_path)

# 確保 geojson 中有經緯度資料
gdf = gdf[gdf.geometry.apply(lambda x: isinstance(x, Point))]

# 建立一個函數來根據車站名稱找到對應的經緯度
def get_coordinates_for_station(station_name):
    # 查找 geojson 中與車站名稱匹配的經緯度
    match = gdf[gdf['station_name'] == station_name]
    if not match.empty:
        return match.geometry.values[0].x, match.geometry.values[0].y  # (longitude, latitude)
    return None

# 定義一個函數來畫出路線圖
def plot_route_on_map(route_data, map_center, route_name):
    # 創建 Folium 地圖，設置地圖中心為基隆市
    folium_map = folium.Map(location=map_center, zoom_start=14)
    
    # 依次將車站畫在地圖上，並將路線連接
    previous_coords = None
    for _, row in route_data.iterrows():
        station_name = row['車站名稱']
        coords = get_coordinates_for_station(station_name)
        if coords:
            folium.Marker(location=coords, popup=station_name).add_to(folium_map)
            
            # 畫出車站之間的連線
            if previous_coords:
                folium.PolyLine([previous_coords, coords], color='blue', weight=2.5, opacity=1).add_to(folium_map)
            previous_coords = coords

    # 儲存地圖為 HTML 檔案
    folium_map.save(f"{route_name}_route_map.html")
    print(f"{route_name} 路線地圖已儲存為 {route_name}_route_map.html")

# 假設去程的起始位置為基隆市中心經緯度
keelung_center_coords = [25.127, 121.739]  # 基隆市大約的經緯度

# 畫出基隆路幹線去程路線圖
plot_route_on_map(go_df, keelung_center_coords, '基隆路幹線去程')

# 畫出基隆路幹線回程路線圖
plot_route_on_map(back_df, keelung_center_coords, '基隆路幹線回程')

# 如果你有承德幹線的車站資料，也可以依照相同方法畫出
