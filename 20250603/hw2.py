# -*- coding: utf-8 -*-
import os
import re
import pandas as pd
from playwright.sync_api import sync_playwright

class taipei_route_list:
    def __init__(self, working_directory: str = 'data'):
        self.working_directory = working_directory
        os.makedirs(self.working_directory, exist_ok=True)
        self.url = 'https://ebus.gov.taipei/ebus?ct=all'
        self.content = None
        self._fetch_content()

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
            raise ValueError("無法解析公車路線")
        df = pd.DataFrame(matches, columns=["route_id", "route_name"])
        return df

class taipei_route_info:
    def __init__(self, route_id: str, direction: str = 'go'):
        self.route_id = route_id
        self.direction = direction
        self.url = f'https://ebus.gov.taipei/Route/StopsOfRoute?routeid={route_id}'
        self.content = None
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

    def parse_stop_names(self):
        pattern = re.compile(
            r'<span class="auto-list-stationlist-number">\s*(\d+)</span>\s*'
            r'<span class="auto-list-stationlist-place">(.*?)</span>',
            re.DOTALL
        )
        matches = pattern.findall(self.content)
        stop_names = [name.strip() for _, name in sorted(matches, key=lambda x: int(x[0]))]
        return stop_names

if __name__ == "__main__":
    route_list = taipei_route_list()
    df_routes = route_list.parse_route_list()

    all_go = []
    all_come = []

    for _, row in df_routes.iterrows():
        route_id = row['route_id']
        route_name = row['route_name']

        for direction in ['go', 'come']:
            try:
                info = taipei_route_info(route_id, direction=direction)
                stop_names = info.parse_stop_names()
                record = {
                    'route_id': route_id,
                    'route_name': route_name
                }
                for i, stop in enumerate(stop_names, start=1):
                    record[f'stop_{i}'] = stop
                if direction == 'go':
                    all_go.append(record)
                else:
                    all_come.append(record)
                print(f"✅ {route_id} {direction} 完成，共 {len(stop_names)} 站")
            except Exception as e:
                print(f"❌ {route_id} {direction} 失敗：{e}")
                continue

    # 匯出 CSV
    if all_go:
        pd.DataFrame(all_go).to_csv("route_go.csv", index=False, encoding='utf-8-sig')
        print("📁 route_go.csv 匯出完成")

    if all_come:
        pd.DataFrame(all_come).to_csv("route_come.csv", index=False, encoding='utf-8-sig')
        print("📁 route_come.csv 匯出完成")
