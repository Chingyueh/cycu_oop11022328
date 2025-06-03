# -*- coding: utf-8 -*-
import os
import re
import pandas as pd

# 新增 playwright 安裝檢查
try:
    from playwright.sync_api import sync_playwright
except ModuleNotFoundError:
    print("未安裝 'playwright' 模組，正在嘗試安裝...")
    os.system("pip install playwright")
    from playwright.sync_api import sync_playwright
    print("請執行以下命令初始化 playwright：")
    print("playwright install")
    exit(1)

from sqlalchemy import create_engine, Column, String, Float, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# ======================== 公車路線列表 ========================
class taipei_route_list:
    def __init__(self, working_directory: str = 'data'):
        self.working_directory = working_directory
        os.makedirs(self.working_directory, exist_ok=True)
        self.url = 'https://ebus.gov.taipei/ebus?ct=all'
        self.content = None
        self._fetch_content()

        Base = declarative_base()

        class bus_route_orm(Base):
            __tablename__ = 'data_route_list'
            route_id = Column(String, primary_key=True)
            route_name = Column(String)
            route_data_updated = Column(Integer, default=0)

        self.orm = bus_route_orm
        self.engine = create_engine(f'sqlite:///{self.working_directory}/hermes_ebus_taipei.sqlite3')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def _fetch_content(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url)
            page.wait_for_timeout(3000)
            self.content = page.content()
            browser.close()

    def parse_route_list(self) -> pd.DataFrame:
        pattern = r'<li><a href="javascript:go\(\'(.*?)\'\)">(.*?)</a></li>'
        matches = re.findall(pattern, self.content, re.DOTALL)
        if not matches:
            raise ValueError("無法解析公車路線列表")
        self.dataframe = pd.DataFrame(matches, columns=["route_id", "route_name"])
        return self.dataframe

    def save_to_database(self):
        for _, row in self.dataframe.iterrows():
            self.session.merge(self.orm(route_id=row['route_id'], route_name=row['route_name']))
        self.session.commit()

    def set_route_data_updated(self, route_id: str, route_data_updated: int = 1):
        self.session.query(self.orm).filter_by(route_id=route_id).update({"route_data_updated": route_data_updated})
        self.session.commit()

    def set_route_data_unexcepted(self, route_id: str):
        self.set_route_data_updated(route_id, route_data_updated=2)

    def __del__(self):
        self.session.close()
        self.engine.dispose()

# ======================== 公車站牌資訊 ========================
class taipei_route_info:
    def __init__(self, route_id: str, direction: str = 'go', working_directory: str = 'data'):
        self.route_id = route_id
        self.direction = direction
        self.url = f'https://ebus.gov.taipei/Route/StopsOfRoute?routeid={route_id}'
        self.content = None
        self.working_directory = working_directory

        if self.direction not in ['go', 'come']:
            raise ValueError("方向只能是 'go' 或 'come'")

        self._fetch_content()

    def _fetch_content(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url)
            if self.direction == 'come':
                try:
                    page.click('a.stationlist-come-go-gray.stationlist-come')
                except:
                    pass
            page.wait_for_timeout(3000)
            self.content = page.content()
            browser.close()

    def parse_route_info(self) -> pd.DataFrame:
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
            raise ValueError(f"無法解析公車站牌：{self.route_id}-{self.direction}")
        df = pd.DataFrame(matches, columns=["arrival_info", "stop_number", "stop_name", "stop_id", "latitude", "longitude"])
        df["direction"] = self.direction
        df["route_id"] = self.route_id
        df["stop_number"] = df["stop_number"].astype(int)
        return df

# ======================== 主程式 ========================
if __name__ == "__main__":
    route_list = taipei_route_list()
    df_routes = route_list.parse_route_list()
    route_list.save_to_database()

    all_go = []
    all_come = []

    for _, row in df_routes.iterrows():
        route_id = row['route_id']
        route_name = row['route_name']

        for direction in ['go', 'come']:
            try:
                route_info = taipei_route_info(route_id, direction=direction)
                df = route_info.parse_route_info()
                df['route_name'] = route_name

                if direction == 'go':
                    all_go.append(df)
                else:
                    all_come.append(df)

                route_list.set_route_data_updated(route_id)
                print(f"✅ {route_id} {direction} 完成，共 {len(df)} 站")

            except Exception as e:
                print(f"❌ {route_id} {direction} 錯誤：{e}")
                route_list.set_route_data_unexcepted(route_id)

    # 輸出 CSV
    if all_go:
        df_go = pd.concat(all_go, ignore_index=True)
        df_go[['route_id', 'route_name', 'stop_number', 'stop_name']].to_csv("route_go.csv", index=False, encoding='utf-8-sig')
        print("📁 route_go.csv 輸出完成")

    if all_come:
        df_come = pd.concat(all_come, ignore_index=True)
        df_come[['route_id', 'route_name', 'stop_number', 'stop_name']].to_csv("route_come.csv", index=False, encoding='utf-8-sig')
        print("📁 route_come.csv 輸出完成")
