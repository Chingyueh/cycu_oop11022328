# -*- coding: utf-8 -*-
"""
This module retrieves bus stop data for a specific route and direction from the Taipei eBus website,
saves the rendered HTML and CSV file, and stores the parsed data in a SQLite database.
"""

import re
import pandas as pd
import folium  # 用於地圖繪製
from folium import CustomIcon  # 用於自訂圖標
from playwright.sync_api import sync_playwright
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


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
        self.content = None
        self.url = f'https://ebus.gov.taipei/Route/StopsOfRoute?routeid={route_id}'
        self.working_directory = working_directory

        if self.direction not in ['go', 'come']:
            raise ValueError("Direction must be 'go' or 'come'")

        self._fetch_content()

    def _fetch_content(self):
        """
        Fetches the webpage content using Playwright and writes the rendered HTML to a local file.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url)

            if self.direction == 'come':
                page.click('a.stationlist-come-go-gray.stationlist-come')

            page.wait_for_timeout(3000)  # Wait for page render
            self.content = page.content()
            browser.close()

        # Save the rendered HTML to a file for inspection
        self.html_file = f"{self.working_directory}/ebus_taipei_{self.route_id}.html"

    def parse_route_info(self) -> pd.DataFrame:
        """
        Parses the fetched HTML content to extract bus stop data.

        Returns:
            pd.DataFrame: DataFrame containing bus stop information.

        Raises:
            ValueError: If no data is found for the route.
        """
        pattern = re.compile(
            r'<li>.*?<span class="auto-list-stationlist-position.*?">(.*?)</span>\s*'
            r'<span class="auto-list-stationlist-number">\s*(\d+)</span>\s*'
            r'<span class="auto-list-stationlist-place">(.*?)</span>.*?'
            r'<input[^>]+name="item\.UniStopId"[^>]+value="(\d+)"[^>]*>.*?'
            r'<input[^>]+name="item\.Latitude"[^>]+value="([\d\.]+)"[^>]*>.*?'
            r'<input[^>]+name="item\.Longitude"[^>]+value="([\d\.]+)"[^>]*>',
            re.DOTALL
        )

        matches = pattern.findall(self.content)
        if not matches:
            raise ValueError(f"No data found for route ID {self.route_id}")

        bus_routes = [m for m in matches]
        self.dataframe = pd.DataFrame(
            bus_routes,
            columns=["arrival_info", "stop_number", "stop_name", "stop_id", "latitude", "longitude"]
        )

        self.dataframe["direction"] = self.direction
        self.dataframe["route_id"] = self.route_id

        return self.dataframe

    def plot_station_on_map(self, stop_number: int):
        """
        Plots a specific bus stop on a map using its stop number.

        Args:
            stop_number (int): The stop number to plot on the map.
        """
        # 確保 dataframe 已初始化
        if not hasattr(self, 'dataframe'):
            raise AttributeError("Dataframe is not initialized. Please call parse_route_info() first.")

        # 找到指定的站點
        stop_data = self.dataframe[self.dataframe['stop_number'] == str(stop_number)]
        if stop_data.empty:
            print(f"Stop number {stop_number} not found.")
            return

        # 獲取站點的經緯度和名稱
        stop_name = stop_data.iloc[0]['stop_name']
        latitude = float(stop_data.iloc[0]['latitude'])
        longitude = float(stop_data.iloc[0]['longitude'])

        # 建立地圖，並將地圖中心設置為該站點
        map_center = [latitude, longitude]
        m = folium.Map(location=map_center, zoom_start=15)

        # 自訂人的圖標
        person_icon = CustomIcon(
            icon_image=r"C:/Users/User/Desktop/cycu_oop11022328/20250429/mei.jpg",
            icon_size=(50, 50)  # 圖片大小
        )

        # 在地圖上添加小人標記
        folium.Marker(
            location=map_center,
            popup=f"Stop: {stop_name} (#{stop_number})",
            icon=person_icon
        ).add_to(m)

        # 將地圖保存為 HTML 文件
        map_file = f"{self.working_directory}/stop_{stop_number}_map.html"
        m.save(map_file)
        print(f"Map for stop {stop_number} saved to {map_file}.")


if __name__ == "__main__":
    # 測試程式
    route_info = taipei_route_info(route_id="0161000900", direction="go")
    
    # 初始化 dataframe
    try:
        route_info.parse_route_info()
    except ValueError as e:
        print(f"Error parsing route info: {e}")
        exit(1)
    
    # 輸入站牌號碼
    stop_number = int(input("Enter the stop number to plot on the map: "))
    
    # 繪製地圖
    route_info.plot_station_on_map(stop_number)