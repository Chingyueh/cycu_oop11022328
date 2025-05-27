import json
import re
import pandas as pd
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import geopandas as gpd
import os
import requests

class taipei_route_info:
    """
    用於處理指定公車路線的站點資料，解析 WKT 格式並將資料儲存。
    """
    def __init__(self, route_id: str, direction: str = 'go', working_directory: str = 'data'):
        self.route_id = route_id
        self.direction = direction
        self.content = None
        self.url = f'https://ebus.gov.taipei/Route/StopsOfRoute?routeid={route_id}'
        self.working_directory = working_directory

        if self.direction not in ['go', 'come']:
            raise ValueError("Direction must be 'go' or 'come'")

        self.html_file = f"{self.working_directory}/ebus_taipei_{self.route_id}.html"
        
        # 若檔案不存在，自動下載
        if not os.path.exists(self.html_file):
            print(f"檔案 {self.html_file} 不存在，正在下載...")
            self.download_html()

        # 讀取已經儲存的 HTML 檔案內容
        with open(self.html_file, 'r', encoding='utf-8') as file:
            self.content = file.read()

    def download_html(self):
        """
        嘗試下載缺少的 HTML 檔案並儲存。
        """
        response = requests.get(self.url)
        if response.status_code == 200:
            os.makedirs(self.working_directory, exist_ok=True)
            with open(self.html_file, 'w', encoding='utf-8') as file:
                file.write(response.text)
            print(f"HTML 檔案已下載並儲存：{self.html_file}")
        else:
            print(f"下載 HTML 檔案失敗，路線 {self.route_id}，HTTP 狀態碼：{response.status_code}")

    def parse_wkt_fields(self) -> dict:
        """
        解析 HTML 中的 WKT 欄位，並抓取對應的 WKT 資料。

        返回：
            dict: 含有 WKT 資料的字典，鍵是 wkt 欄位，值是對應的 WKT 字串。
        """
        wkt_dict = {}
        pattern = r'JSON\.stringify\s*\(\s*(\{[\s\S]*?\})\s*\)'
        match = re.search(pattern, self.content)
        if match:
            json_text = match.group(1)
            json_dict = json.loads(json_text)
            for key in json_dict.keys():
                if key.startswith('wkt'):
                    wkt_dict[key] = json_dict[key]
            return wkt_dict
        else:
            return {}

class taipei_route_list:
    """
    用於處理台北市公車路線列表，將路線資料儲存到資料庫中並讀取資料。
    """
    def __init__(self, working_directory: str = 'data'):
        self.working_directory = working_directory
        self.url = 'https://ebus.gov.taipei/ebus?ct=all'
        
        Base = declarative_base()

        class bus_route_orm(Base):
            __tablename__ = 'data_route_list'
            route_id = Column(String, primary_key=True)
            route_name = Column(String)
            route_data_updated = Column(Integer, default=0)

        self.orm = bus_route_orm

        # 創建資料庫引擎
        self.engine = create_engine(f'sqlite:///{self.working_directory}/hermes_ebus_taipei.sqlite3')
        self.engine.connect()
        Base.metadata.create_all(self.engine)

        # 創建資料庫會話
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def read_from_database(self) -> pd.DataFrame:
        """
        從資料庫讀取所有路線資料，並返回 DataFrame 格式。

        返回：
            pd.DataFrame: 公車路線資料的 DataFrame。
        """
        query = self.session.query(self.orm)
        return pd.read_sql(query.statement, self.session.bind)


if __name__ == "__main__":
    # 初始化路線列表處理類別
    route_list = taipei_route_list()
    geo_df = pd.DataFrame()  # 用於儲存所有路線的資料

    # 從資料庫中讀取所有路線資料
    route_df = route_list.read_from_database()

    # 遍歷所有路線資料並處理
    for _, row in route_df.iterrows():
        try:
            route_info = taipei_route_info(route_id=row["route_id"], direction="go")
            dict_wkt = route_info.parse_wkt_fields()

            # 把解析後的 WKT 資料轉換成 DataFrame
            df = pd.DataFrame(dict_wkt.items(), columns=['wkt_id', 'wkt_string'])
            df['route_id'] = route_info.route_id
            df['route_name'] = row["route_name"]

            # 轉換為 GeoDataFrame
            df['geometry'] = gpd.GeoSeries.from_wkt(df['wkt_string'])
            gdf = gpd.GeoDataFrame(df, geometry='geometry')

            # 設定 CRS 為 WGS84
            gdf.crs = 'EPSG:4326'
            gdf.set_geometry('geometry', inplace=True)

            # 合併所有的 GeoDataFrame 資料
            geo_df = pd.concat([geo_df, gdf], ignore_index=True)

            print(f"已處理路線 ID: {route_info.route_id}, 共有 {len(dict_wkt)} 個 WKT 欄位")

        except Exception as e:
            print(f"處理路線 {row['route_name']} 時發生錯誤: {e}")

    # 儲存結果為 CSV 檔案
    csv_path = f"{route_list.working_directory}/ebus_taipei_routes.csv"
    try:
        geo_df.to_csv(csv_path, index=False)
        print("CSV 檔案已儲存完成！")
    except PermissionError:
        print(f"無法寫入 {csv_path}，請確認檔案未被其他程式(如Excel)開啟，或檢查權限。")
