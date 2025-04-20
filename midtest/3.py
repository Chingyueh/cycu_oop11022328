from playwright.sync_api import sync_playwright
import pandas as pd
import time


def parse_direction(direction_div):
    results = []
    li_elements = direction_div.query_selector_all("li")
    for li in li_elements:
        time_element = li.query_selector(
            "span.auto-list-stationlist-position.auto-list-stationlist-position-time")
        if not time_element:
            time_element = li.query_selector(
                "span.auto-list-stationlist-position.auto-list-stationlist-position-now")
            arrival_time = "進站中" if time_element else ""
        else:
            arrival_time = time_element.inner_text() if time_element else ""
        seq_element = li.query_selector("span.auto-list-stationlist-number")
        seq_num = seq_element.inner_text() if seq_element else ""
        name_element = li.query_selector("span.auto-list-stationlist-place")
        stop_name = name_element.inner_text() if name_element else ""
        id_element = li.query_selector("input#item_UniStopId")
        stop_id = id_element.get_attribute("value") if id_element else ""
        lat_element = li.query_selector("input[name='item.Latitude']")
        latitude = lat_element.get_attribute("value") if lat_element else ""
        lng_element = li.query_selector("input[name='item.Longitude']")
        longitude = lng_element.get_attribute("value") if lng_element else ""
        results.append([arrival_time, seq_num, stop_name,
                       stop_id, latitude, longitude])
    return results


def scrape_bus_route(routeid="0100000A00"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = f"https://ebus.gov.taipei/Route/StopsOfRoute?routeid={routeid}"
        page.goto(url)
        page.wait_for_selector("#GoDirectionRoute")
        time.sleep(2)

        # 1. 去程
        page.click("a.stationlist-go")
        time.sleep(1)
        go_div = page.query_selector("#GoDirectionRoute")
        go_data = parse_direction(go_div)
        go_df = pd.DataFrame(
            go_data, columns=["公車到達時間", "車站序號", "車站名稱", "車站編號", "latitude", "longitude"])
        go_df.to_csv(f"bus_stops_{routeid}_go.csv",
                     index=False, encoding="utf-8-sig")
        print(f"已儲存 bus_stops_{routeid}_go.csv")
        print("去程：")
        print(go_df)

        # 2. 回程
        page.click("a.stationlist-come")
        page.wait_for_selector("#BackDirectionRoute", state="visible")
        time.sleep(1)
        back_div = page.query_selector("#BackDirectionRoute")
        back_data = parse_direction(back_div)
        back_df = pd.DataFrame(back_data, columns=[
                               "公車到達時間", "車站序號", "車站名稱", "車站編號", "latitude", "longitude"])
        back_df.to_csv(f"bus_stops_{routeid}_back.csv",
                       index=False, encoding="utf-8-sig")
        print(f"已儲存 bus_stops_{routeid}_back.csv")
        print("回程：")
        print(back_df)

        browser.close()
        return go_df, back_df


if __name__ == "__main__":
    route_id = "0100000A00"  # 你可以自行更換
    go_df, back_df = scrape_bus_route(route_id)