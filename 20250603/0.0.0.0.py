from playwright.sync_api import sync_playwright
import pandas as pd
import time
import os

def parse_stop_names(direction_div):
    stop_names = []
    li_elements = direction_div.query_selector_all("li")
    for li in li_elements:
        name_element = li.query_selector("span.auto-list-stationlist-place")
        stop_name = name_element.inner_text().strip() if name_element else ""
        if stop_name:
            stop_names.append(stop_name)
    return stop_names

def scrape_route_stops(route_id: str):
    result_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = f"https://ebus.gov.taipei/Route/StopsOfRoute?routeid={route_id}"
        print(f"🔍 抓取中：{url}")
        page.goto(url)
        page.wait_for_selector("#GoDirectionRoute")
        time.sleep(2)

        # 嘗試抓路線名稱（標題）
        try:
            route_name = page.locator("h3.route-name").inner_text().strip()
        except:
            route_name = ""

        # 去程
        page.click("a.stationlist-go")
        page.wait_for_selector("#GoDirectionRoute li")
        go_div = page.query_selector("#GoDirectionRoute")
        go_stops = parse_stop_names(go_div)
        result_rows.append({
            "route_id": route_id,
            "route_name": route_name,
            "direction": "go",
            "stops": " > ".join(go_stops)
        })

        # 回程
        page.click("a.stationlist-come")
        page.wait_for_selector("#BackDirectionRoute li")
        back_div = page.query_selector("#BackDirectionRoute")
        back_stops = parse_stop_names(back_div)
        result_rows.append({
            "route_id": route_id,
            "route_name": route_name,
            "direction": "come",
            "stops": " > ".join(back_stops)
        })

        browser.close()

    return result_rows

def build_route_summary(route_ids: list, output_csv: str = "bus_route_summary.csv"):
    all_data = []

    for route_id in route_ids:
        try:
            rows = scrape_route_stops(route_id)
            all_data.extend(rows)
        except Exception as e:
            print(f"⚠️  抓取 {route_id} 時發生錯誤：{e}")

    df = pd.DataFrame(all_data)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"✅ 匯出完成：已儲存為 {output_csv}")

if __name__ == "__main__":
    # ✅ 可自訂一批 route_id
    route_ids = [
        "0471001700",  # 新九號
        "0610001000",  # 307
        "0880011000",  # 284
        # ... 更多 ID 可加上去
    ]
    build_route_summary(route_ids)
