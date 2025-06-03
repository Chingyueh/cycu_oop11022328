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

if __name__ == "__main__":
    route_list = taipei_route_list()
    df = route_list.parse_route_list()
    df.to_csv("taipei_routes.csv", index=False, encoding="utf-8-sig")
    print("✅ taipei_routes.csv 匯出完成")
