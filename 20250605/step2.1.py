import pandas as pd
from playwright.sync_api import sync_playwright
import time
import matplotlib.pyplot as plt
import geopandas as gpd

# ====== 把這個函式搬到這裡 ======
def visualize_route_from_csv(route_id, csv_path, save_path=None, basemap_path=None):
    df = pd.read_csv(csv_path)
    plt.figure(figsize=(10, 8))
    ax = plt.gca()
    if basemap_path:
        base = gpd.read_file(basemap_path)
        print("底圖 CRS:", base.crs)
        if base.crs is None:
            # 假設你的底圖是 TWD97/TM2
            base.set_crs(epsg=3826, inplace=True)
        if base.crs.to_epsg() != 4326:
            base = base.to_crs(epsg=4326)
        base.plot(ax=ax, color='white', edgecolor='gray', alpha=0.5)
    print("站點經緯度範圍：")
    print("lat:", df['lat'].min(), "~", df['lat'].max())
    print("lon:", df['lon'].min(), "~", df['lon'].max())
    plt.plot(df['lon'], df['lat'], marker='o', color='blue', linewidth=2, label=f'Route {route_id}')
    for i, row in df.iterrows():
        plt.text(row['lon'], row['lat'], row['stop_name'], fontsize=8)
    plt.xlabel('經度')
    plt.ylabel('緯度')
    plt.title(f'公車路線 {route_id}')
    plt.legend()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
        print(f"🗺️ 地圖已儲存為 {save_path}")
    plt.show()

def convert_to_long_format(file_path, direction):
    # 讀檔案
    df = pd.read_csv(file_path)
    
    # 尋找所有站名欄位（像 stop_1, stop_2, ...）
    stop_columns = [col for col in df.columns if col.startswith("stop_")]
    
    # 用 melt 展平
    long_df = df.melt(id_vars=["route_id", "route_name"],
                      value_vars=stop_columns,
                      var_name="stop_sequence_raw",
                      value_name="stop_name")
    
    # 抽出 stop_sequence 的數字並轉成 int
    long_df["stop_sequence"] = long_df["stop_sequence_raw"].str.extract(r"(\d+)").astype(int)
    
    # 加上方向欄位
    long_df["direction"] = direction
    
    # 移除空值
    long_df = long_df.dropna(subset=["stop_name"])
    
    # 最終欄位順序
    long_df = long_df[["route_id", "route_name", "stop_sequence", "stop_name", "direction"]]
    
    return long_df

# 設定檔案路徑（根據你的實際路徑調整）
go_path = "route_go.csv"
come_path = "route_come.csv"

# 分別轉換
go_df = convert_to_long_format(go_path, "go")
come_df = convert_to_long_format(come_path, "come")

# 合併兩份
full_df = pd.concat([go_df, come_df], ignore_index=True)

# 輸出成新的 CSV
full_df.to_csv("C:/Users/user/Desktop/cycu_oop11022328/20250605/full_route_stops.csv", index=False)

print("✅ 轉換成功！檔案儲存為 full_route_stops.csv")


# ---------- 爬蟲工具：解析站點資訊 ----------
def parse_direction(direction_div):
    results = []
    li_elements = direction_div.query_selector_all("li")
    for li in li_elements:
        time_element = li.query_selector("span.auto-list-stationlist-position.auto-list-stationlist-position-time")
        if not time_element:
            time_element = li.query_selector("span.auto-list-stationlist-position.auto-list-stationlist-position-now")
            arrival_time = "進站中" if time_element else ""
        else:
            arrival_time = time_element.inner_text()

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
        results.append([arrival_time, seq_num, stop_name, stop_id, latitude, longitude])
    return results

# ---------- 爬蟲主程式 ----------
def scrape_real_time(routeid):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = f"https://ebus.gov.taipei/Route/StopsOfRoute?routeid={routeid}"
        page.goto(url)
        page.wait_for_selector("#GoDirectionRoute")
        time.sleep(2)

        # 去程
        page.click("a.stationlist-go")
        time.sleep(1)
        go_div = page.query_selector("#GoDirectionRoute")
        go_data = parse_direction(go_div)
        go_df = pd.DataFrame(go_data, columns=["到站時間", "站序", "站名", "站ID", "lat", "lon"])

        # 回程
        page.click("a.stationlist-come")
        page.wait_for_selector("#BackDirectionRoute", state="visible")
        time.sleep(1)
        back_div = page.query_selector("#BackDirectionRoute")
        back_data = parse_direction(back_div)
        back_df = pd.DataFrame(back_data, columns=["到站時間", "站序", "站名", "站ID", "lat", "lon"])

        browser.close()
        return go_df, back_df

# ---------- 查詢路線 ----------
def find_bus_routes_from_df(df, start_stop, end_stop):
    result = []

    filtered = df[df['stop_name'].isin([start_stop, end_stop])]
    for (route_id, direction), group in filtered.groupby(['route_id', 'direction']):
        stops = group.sort_values('stop_sequence')
        stop_names = stops['stop_name'].tolist()

        if start_stop in stop_names and end_stop in stop_names:
            start_seq = stops[stops['stop_name'] == start_stop]['stop_sequence'].min()
            end_seq = stops[stops['stop_name'] == end_stop]['stop_sequence'].min()

            if start_seq < end_seq:
                route_name = df[(df['route_id'] == route_id)]['route_name'].iloc[0]
                result.append({
                    'route_id': route_id,
                    'route_name': route_name,
                    'direction': direction,
                    'start_seq': start_seq,
                    'end_seq': end_seq
                })
    return pd.DataFrame(result)

# ---------- 主程式 ----------
if __name__ == "__main__":
    csv_path = "full_route_stops.csv"  # 已整理好的路線站點 CSV
    start_stop = input("請輸入出發站：").strip()
    end_stop = input("請輸入目的站：").strip()

    df = pd.read_csv(csv_path)

    match_routes = find_bus_routes_from_df(df, start_stop, end_stop)

    if match_routes.empty:
        print("😢 找不到可搭乘的公車路線…")
    else:
        print("\n✅ 可以搭乘以下公車路線：")
        for i, row in match_routes.reset_index(drop=True).iterrows():
            direction_text = "去程" if row["direction"] == "go" else "回程"
            print(f"{i}. 🚍 {row['route_name']}（{direction_text}）")

        # 讓使用者選擇要查詢的路線編號
        while True:
            try:
                choice = int(input("\n請選擇公車路線編號："))
                if choice < 0 or choice >= len(match_routes):
                    print("❌ 輸入錯誤，請輸入有效的路線編號。")
                    continue
                break
            except ValueError:
                print("❌ 請輸入數字。")

        selected = match_routes.reset_index(drop=True).iloc[choice]
        print(f"\n🔍 正在查詢 {selected['route_name']} ({selected['direction']}) 的即時動態...")

        go_df, back_df = scrape_real_time(selected["route_id"])
        if selected["direction"] == "go":
            print("\n📍 即時動態（去程）：")
            print(go_df)
        else:
            print("\n📍 即時動態（回程）：")
            print(back_df)

        # === 新增：畫出使用者選擇的路線地圖 ===
        stops_df = go_df if selected["direction"] == "go" else back_df
        stops_df = stops_df.rename(columns={"lat": "lat", "lon": "lon", "站名": "stop_name"})
        stops_df["lat"] = stops_df["lat"].astype(float)
        stops_df["lon"] = stops_df["lon"].astype(float)
        stops_df["stop_sequence"] = stops_df["站序"].astype(int)
        stops_df = stops_df.sort_values("stop_sequence")

        # 建立暫存檔案
        temp_csv = "temp_selected_route.csv"
        stops_df.to_csv(temp_csv, index=False, encoding="utf-8-sig")

        # 畫圖
        visualize_route_from_csv(
            route_id=selected["route_id"],
            csv_path=temp_csv,
            save_path=f"route_{selected['route_id']}_{selected['direction']}.png",
            basemap_path="C:/Users/user/Desktop/cycu_oop11022328/20250605/Village_Sanhe.shp"
        )



