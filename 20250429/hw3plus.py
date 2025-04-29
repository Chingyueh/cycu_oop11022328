# -*- coding: utf-8 -*-
"""
This module retrieves bus stop data for a specific route and direction from the Taipei eBus website,
saves the rendered HTML and CSV file, and stores the parsed data in a SQLite database.
"""

import folium  # 用於地圖繪製
import json  # 用於解析 JSON 格式的資料


class taipei_route_info:
    """
    Manages fetching, parsing, and storing bus stop data for a specified route and direction.
    """

    def __init__(self, route_id: str, direction: str = 'go', working_directory: str = 'data'):
        """
        Initializes the taipei_route_info by setting parameters and fetching the webpage content.

        Args:
            route_id (str): The unique identifier of the bus route.
            direction (str): The direction of the route; must be either 'go' or 'come'.
        """
        self.route_id = route_id
        self.direction = direction
        self.working_directory = working_directory

    def get_bus_data(self, bus_code: str) -> dict:
        """
        Reads bus data from an external file and retrieves information for the specified bus code.

        Args:
            bus_code (str): The bus code to retrieve data for.

        Returns:
            dict: A dictionary containing bus data for the specified bus code.
        """
        data_file = r"C:\Users\User\Desktop\cycu_oop11022328\midtest/3.py"

        try:
            # 假設 3.py 的內容是 JSON 格式的字串，讀取並解析
            with open(data_file, "r", encoding="utf-8") as file:
                bus_data = json.load(file)

            # 根據公車代碼查詢資料
            for bus in bus_data.get("buses", []):
                if bus["bus_code"] == bus_code:
                    return bus

            # 如果找不到對應的公車代碼，回傳空字典
            return {}

        except Exception as e:
            print(f"Error reading bus data: {e}")
            return {}

    def plot_station_on_map(self, bus_code: str):
        """
        Plots a specific bus stop on a map using its bus code.
        Retrieves bus arrival data from an external file.

        Args:
            bus_code (str): The bus code to plot on the map.
        """
        # 模擬站點數據
        stop_name = "北投站"
        latitude = 25.144595
        longitude = 121.492071

        # 從外部檔案獲取公車進站資訊和剩餘時間
        bus_data = self.get_bus_data(bus_code)
        if not bus_data:
            print(f"No data found for bus code: {bus_code}")
            return

        bus_arriving = bus_data.get("bus_arriving", False)
        arrival_time = bus_data.get("arrival_time", None)
        bus_location = bus_data.get("bus_location", [latitude + 0.0002, longitude + 0.0002])

        # 建立地圖，並將地圖中心設置為該站點
        map_center = [latitude, longitude]
        m = folium.Map(location=map_center, zoom_start=15)

        # 在地圖上添加小人標記
        folium.Marker(
            location=map_center,
            popup=f"Stop: {stop_name} (Bus Code: {bus_code})",
            icon=folium.Icon(icon="user", color="blue")
        ).add_to(m)

        # 在小人旁邊畫一個公車
        bus_marker_location = [latitude + 0.0001, longitude + 0.0001]  # 偏移位置
        folium.Marker(
            location=bus_marker_location,
            popup=f"Bus Code: {bus_code}",
            icon=folium.Icon(icon="bus", color="red")
        ).add_to(m)

        # 在公車圖案左邊顯示剩餘到站時間
        if arrival_time is not None:
            time_marker_location = [latitude + 0.0001, longitude - 0.0002]  # 偏移位置
            folium.Marker(
                location=time_marker_location,
                icon=folium.DivIcon(html=f"""
                    <div style="font-size: 14px; font-weight: bold; color: red;">
                        {arrival_time} min
                    </div>
                """)
            ).add_to(m)

        # 如果公車進站，則在該站畫一台公車
        if bus_arriving:
            folium.Marker(
                location=map_center,
                popup=f"Bus arriving at Stop: {stop_name}",
                icon=folium.Icon(icon="bus", color="green")
            ).add_to(m)

        # 將地圖保存為 HTML 文件
        map_file = f"{self.working_directory}/bus_{bus_code}_map.html"
        m.save(map_file)
        print(f"Map for bus code {bus_code} saved to {map_file}.")


if __name__ == "__main__":
    # 測試程式
    bus_code = input("Enter the bus code to plot on the map: ")  # 使用者輸入公車代碼
    route_info = taipei_route_info(route_id="0161000900", direction="go")
    route_info.plot_station_on_map(bus_code)