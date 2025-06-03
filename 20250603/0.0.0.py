import os
import requests
import pandas as pd
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


class taipei_route_list:
    """
    管理台北市公車路線資料庫的 ORM 類別
    """
    def __init__(self, working_directory='data'):
        self.working_directory = working_directory
        os.makedirs(working_directory, exist_ok=True)

        Base = declarative_base()

        class BusRoute(Base):
            __tablename__ = 'data_route_list'
            route_id = Column(String, primary_key=True)
            route_name = Column(String)
            route_data_updated = Column(Integer, default=0)

        self.orm = BusRoute

        self.engine = create_engine(f'sqlite:///{self.working_directory}/hermes_ebus_taipei.sqlite3')
        self.engine.connect()
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def read_from_database(self) -> pd.DataFrame:
        query = self.session.query(self.orm)
        return pd.read_sql(query.statement, self.session.bind)


class taipei_route_info:
    """
    下載並解析單一路線的所有站點資訊（雙向）
    """
    def __init__(self, route_id):
        self.route_id = route_id
        self.url = f'https://ebus.gov.taipei/Route/StopsOfRoute?routeid={self.route_id}'

    def get_stop_list(self) -> pd.DataFrame:
        try:
            response = requests.get(self.url)
            response.encoding = 'utf-8'
            data = response.json()
        except Exception as e:
            print(f"[錯誤] 無法下載資料（route_id={self.route_id}）：{e}")
            return pd.DataFrame()

        stops = []
        for direction_key in ['go', 'come']:
            if direction_key in data:
                for stop in data[direction_key]:
                    stops.append({
                        'route_id': self.route_id,
                        'direction': direction_key,
                        'stop_sequence': stop.get('Seq'),
                        'stop_uid': stop.get('StopUID'),
                        'stop_name': stop.get('StopName', {}).get('Zh_tw')
                    })

        return pd.DataFrame(stops)


if __name__ == '__main__':
    route_list = taipei_route_list()
    route_df = route_list.read_from_database()

    all_stops_df = pd.DataFrame()

    for idx, row in route_df.iterrows():
        route_id = row["route_id"]
        print(f"🔍 下載 {row['route_name']}（route_id={route_id}）的站點清單...")
        route_info = taipei_route_info(route_id)
        stop_df = route_info.get_stop_list()

        if not stop_df.empty:
            all_stops_df = pd.concat([all_stops_df, stop_df], ignore_index=True)

    # 儲存結果
    output_csv = f"{route_list.working_directory}/ebus_taipei_stops_full.csv"
    all_stops_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"\n✅ 所有路線站點資料已儲存至：{output_csv}")
