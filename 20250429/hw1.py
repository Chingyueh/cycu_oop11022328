# -*- coding: utf-8 -*-
"""
This module retrieves bus stop data for a specific route and direction from the Taipei eBus website,
saves the rendered HTML and CSV file, and stores the parsed data in a SQLite database.
"""

import re
import pandas as pd
import folium  # 用於地圖繪製
from playwright.sync_api import sync_playwright
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


class taipei_route_list:
    """
    Manages fetching, parsing, and storing route data for Taipei eBus.
    """

    def __init__(self, working_directory: str = 'data'):
        """
        Initializes the taipei_route_list, fetches webpage content,
        configures the ORM, and sets up the SQLite database.

        Args:
            working_directory (str): Directory to store the HTML and database files.
        """
        self.working_directory = working_directory
        self.url = 'https://ebus.gov.taipei/ebus?ct=all'
        self.content = None

        # Fetch webpage content
        self._fetch_content()

        # Setup ORM base and table
        Base = declarative_base()

        class bus_route_orm(Base):
            __tablename__ = 'data_route_list'

            route_id = Column(String, primary_key=True)
            route_name = Column(String)
            route_data_updated = Column(Integer, default=0)

        self.orm = bus_route_orm

        # Create and connect to the SQLite engine
        self.engine = create_engine(f'sqlite:///{self.working_directory}/hermes_ebus_taipei.sqlite3')
        self.engine.connect()
        Base.metadata.create_all(self.engine)

        # Create session
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def _fetch_content(self):
        """
        Fetches the webpage content using Playwright and saves it as a local HTML file.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url)
            page.wait_for_timeout(3000)  # Wait for the page to load
            self.content = page.content()
            browser.close()

        # Save the rendered HTML to a file for inspection
        html_file_path = f'{self.working_directory}/hermes_ebus_taipei_route_list.html'
        with open(html_file_path, "w", encoding="utf-8") as file:
            file.write(self.content)

    def parse_route_list(self) -> pd.DataFrame:
        """
        Parses bus route data from the fetched HTML content.

        Returns:
            pd.DataFrame: DataFrame containing bus route IDs and names.

        Raises:
            ValueError: If no route data is found.
        """
        pattern = r'<li><a href="javascript:go\(\'(.*?)\'\)">(.*?)</a></li>'
        matches = re.findall(pattern, self.content, re.DOTALL)

        if not matches:
            raise ValueError("No data found for route table")

        bus_routes = [(route_id, route_name.strip()) for route_id, route_name in matches]
        self.dataframe = pd.DataFrame(bus_routes, columns=["route_id", "route_name"])
        return self.dataframe

    def save_to_database(self):
        """
        Saves the parsed bus route data to the SQLite database via SQLAlchemy ORM.
        """
        for _, row in self.dataframe.iterrows():
            self.session.merge(self.orm(route_id=row['route_id'], route_name=row['route_name']))

        self.session.commit()

    def read_from_database(self) -> pd.DataFrame:
        """
        Reads bus route data from the SQLite database.

        Returns:
            pd.DataFrame: DataFrame containing bus route data.
        """
        query = self.session.query(self.orm)
        self.db_dataframe = pd.read_sql(query.statement, self.session.bind)
        return self.db_dataframe

    def set_route_data_updated(self, route_id: str, route_data_updated: int = 1):
        """
        Sets the route_data_updated flag in the database.

        Args:
            route_id (str): The ID of the bus route.
            route_data_updated (bool): The value to set for the route_data_updated flag.
        """
        self.session.query(self.orm).filter_by(route_id=route_id).update({"route_data_updated": route_data_updated})
        self.session.commit()

    def set_route_data_unexcepted(self, route_id: str):
        self.session.query(self.orm).filter_by(route_id=route_id).update({"route_data_updated": 2})
        self.session.commit()

    def __del__(self):
        """
        Closes the session and engine when the object is deleted.
        """
        if hasattr(self, 'session') and self.session is not None:
            self.session.close()
        if hasattr(self, 'engine') and self.engine is not None:
            self.engine.dispose()


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

    def save_to_database(self):
        """
        Saves the parsed bus stop data to the SQLite database.
        """
        db_file = f"{self.working_directory}/hermes_ebus_taipei.sqlite3"
        engine = create_engine(f"sqlite:///{db_file}")
        Base = declarative_base()

        class bus_stop_orm(Base):
            __tablename__ = "data_route_info_busstop"
            stop_id = Column(Integer)
            arrival_info = Column(String)
            stop_number = Column(Integer, primary_key=True)
            stop_name = Column(String)
            latitude = Column(Float)
            longitude = Column(Float)
            direction = Column(String, primary_key=True)
            route_id = Column(String, primary_key=True)

        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        for _, row in self.dataframe.iterrows():
            session.merge(bus_stop_orm(
                stop_id=row["stop_id"],
                arrival_info=row["arrival_info"],
                stop_number=row["stop_number"],
                stop_name=row["stop_name"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                direction=row["direction"],
                route_id=row["route_id"]
            ))

        session.commit()
        session.close()

    def plot_station_on_map(self, stop_number: int):
        """
        Plots a specific bus stop on a map using its stop number.

        Args:
            stop_number (int): The stop number to plot on the map.
        """
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

        # 在地圖上添加小人標記
        folium.Marker(
            location=map_center,
            popup=f"Stop: {stop_name} (#{stop_number})",
            icon=folium.Icon(icon="user", color="blue")
        ).add_to(m)

        # 將地圖保存為 HTML 文件
        map_file = f"{self.working_directory}/stop_{stop_number}_map.html"
        m.save(map_file)
        print(f"Map for stop {stop_number} saved to {map_file}.")


if __name__ == "__main__":
    # Initialize and process route data
    route_list = taipei_route_list()
    route_list.parse_route_list()
    route_list.save_to_database()

    bus1 = '0161000900'  # 承德幹線
    bus2 = '0161001500'  # 基隆幹線

    bus_list = [bus1]

    for route_id in bus_list:
        try:
            route_info = taipei_route_info(route_id, direction="go")
            route_info.parse_route_info()
            route_info.save_to_database()

            for index, row in route_info.dataframe.iterrows():
                print(f"Stop Number: {row['stop_number']}, Stop Name: {row['stop_name']}, "
                      f"Latitude: {row['latitude']}, Longitude: {row['longitude']}")

            # 讓使用者輸入站號碼
            stop_number = int(input("Enter the stop number to plot on the map: "))
            route_info.plot_station_on_map(stop_number)

            route_list.set_route_data_updated(route_id)
            print(f"Route data for {route_id} updated.")

        except Exception as e:
            print(f"Error processing route {route_id}: {e}")
            route_list.set_route_data_unexcepted(route_id)
            continue