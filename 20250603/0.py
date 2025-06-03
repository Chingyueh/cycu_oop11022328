from playwright.sync_api import sync_playwright
import pandas as pd
import sqlite3
import os
import time


def parse_direction(direction_div, direction):
    results = []
    li_elements = direction_div.query_selector_all("li")
    for li in li_elements:
        seq_element = li.query_selector("span.auto-list-stationlist-number")
        seq_num = int(seq_element.inner_text()) if seq_element else -1

        name_element = li.query_selector("span.auto-list-stationlist-place")
        stop_name = name_element.inner_text().strip() if name_element else ""

        id_element = li.query_selector("input#item_UniStopId")
        stop_id = id_element.get_attribute("value") if id_element else ""

        results.append((stop_id, stop_name, direction, seq_num))
    return results


def scrape_and_save_to_sqlite(route_id: str, db_path: str = "hermes_ebus_taipei.sqlite3"):
    all_stops = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = f"https://ebus.gov.taipei/Route/StopsOfRoute?routeid={route_id}"
        print(f"🔍 正在抓取 {url}")
        page.goto(url)
        page.wait_for_selector("#GoDirectionRoute")
        time.sleep(2)

        # 去程
        page.click("a.stationlist-go")
        time.sleep(1)
        go_div = page.query_selector("#GoDirectionRoute")
        go_stops = parse_direction(go_div, direction="go")

        # 回程
        page.click("a.stationlist-come")
        page.wait_for_selector("#BackDirectionRoute", state="visible")
        time.sleep(1)
        back_div = page.query_selector("#BackDirectionRoute")
        back_stops = parse_direction(back_div, direction="come")

        all_stops.extend(go_stops)
        all_stops.extend(back_stops)

        browser.close()

    # 連接 SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 建立表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bus_stops (
            stop_uid TEXT,
            stop_name TEXT,
            direction TEXT,
            stop_sequence INTEGER,
            route_id TEXT
        )
    ''')

    # 清除舊資料（如果已存在該路線）
    cursor.execute('DELETE FROM bus_stops WHERE route_id = ?', (route_id,))

    # 插入新資料
    for stop in all_stops:
        cursor.execute('INSERT INTO bus_stops (stop_uid, stop_name, direction, stop_sequence, route_id) VALUES (?, ?, ?, ?, ?)',
                       (stop[0], stop[1], stop[2], stop[3], route_id))
    conn.commit()

    # 匯出 CSV
    df = pd.read_sql_query("SELECT stop_uid, stop_name, direction, stop_sequence FROM bus_stops WHERE route_id = ?", conn, params=(route_id,))
    df.to_csv(f"route_stops_{route_id}.csv", index=False, encoding="utf-8-sig")
    print(f"✅ 完成：已儲存 route_stops_{route_id}.csv 並寫入 SQLite 資料庫")
    conn.close()


if __name__ == "__main__":
    # ✨ 你可以在這裡換其他 route_id
    route_id = "0471001700"  # 新九號停車場-水湳洞
    scrape_and_save_to_sqlite(route_id)

