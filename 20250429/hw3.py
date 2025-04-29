# -*- coding: utf-8 -*-
"""
This module retrieves bus stop data for a specific route and direction from the Taipei eBus website,
saves the rendered HTML and CSV file, and stores the parsed data in a SQLite database.
"""

import folium  # 用於地圖繪製


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

    def plot_station_on_map(self, stop_number: int, bus_arriving: bool = False, arrival_time: int = None):
        """
        Plots a specific bus stop on a map using its stop number.
        Optionally adds a bus icon if the bus is arriving, with arrival time displayed.

        Args:
            stop_number (int): The stop number to plot on the map.
            bus_arriving (bool): Whether to add a bus icon to the map.
            arrival_time (int): The remaining time (in minutes) for the bus to arrive.
        """
        # 模擬站點數據
        stop_name = "北投站"
        latitude = 25.144595
        longitude = 121.492071

        # 建立地圖，並將地圖中心設置為該站點
        map_center = [latitude, longitude]
        m = folium.Map(location=map_center, zoom_start=15)

        # 在地圖上添加小人標記
        folium.Marker(
            location=map_center,
            popup=f"Stop: {stop_name} (#{stop_number})",
            icon=folium.Icon(icon="user", color="blue")
        ).add_to(m)

        # 如果公車進站，添加公車標記和剩餘時間標記
        if bus_arriving:
            # 公車圖標位置
            bus_location = [latitude + 0.0001, longitude + 0.0001]  # 偏移位置
            folium.Marker(
                location=bus_location,
                popup=f"Bus arriving at Stop: {stop_name} (#{stop_number})",
                icon=folium.Icon(icon="bus", color="red")
            ).add_to(m)

            # 剩餘時間標記位置（偏移到公車圖標左邊）
            time_location = [latitude + 0.0001, longitude - 0.0002]  # 偏移位置
            folium.Marker(
                location=time_location,
                icon=folium.DivIcon(html=f"""
                    <div style="font-size: 14px; font-weight: bold; color: red;">
                        {arrival_time} min
                    </div>
                """)
            ).add_to(m)

        # 將地圖保存為 HTML 文件
        map_file = f"{self.working_directory}/stop_{stop_number}_map.html"
        m.save(map_file)
        print(f"Map for stop {stop_number} saved to {map_file}.")


if __name__ == "__main__":
    # 測試程式
    route_info = taipei_route_info(route_id="0161000900", direction="go")
    stop_number = 70
    bus_arriving = True
    arrival_time = 10  # 剩餘到站時間（分鐘）
    route_info.plot_station_on_map(stop_number, bus_arriving, arrival_time)