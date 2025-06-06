import pandas as pd
from playwright.sync_api import sync_playwright
import time

import pandas as pd

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
go_path = "./20250605/route_go.csv"
come_path = "./20250605/route_come.csv"

# 分別轉換
go_df = convert_to_long_format(go_path, "go")
come_df = convert_to_long_format(come_path, "come")

# 合併兩份
full_df = pd.concat([go_df, come_df], ignore_index=True)

# 去除重複資料
full_df = full_df.drop_duplicates()

# 自動判斷方向（同一路線最小序號為 go，最大為 come）
def infer_direction(group):
    min_seq = group['stop_sequence'].min()
    max_seq = group['stop_sequence'].max()
    group['direction'] = group['stop_sequence'].apply(lambda x: 'go' if abs(x - min_seq) < abs(x - max_seq) else 'come')
    return group

full_df = full_df.groupby(['route_id', 'route_name']).apply(infer_direction).reset_index(drop=True)

# 重新排序
full_df = full_df.sort_values(['route_id', 'direction', 'stop_sequence'])

# 儲存為 utf-8-sig，避免 Excel 亂碼
full_df.to_csv("./20250605/full_route_stops.csv", index=False, encoding="utf-8-sig")

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
    csv_path = "./20250605/full_route_stops.csv"  # 已整理好的路線站點 CSV
    start_stop = input("請輸入出發站：").strip()
    end_stop = input("請輸入目的站：").strip()

    # 嘗試用 utf-8-sig 或 big5 讀取，避免亂碼
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="big5")

    # 去除重複資料
    df = df.drop_duplicates()

    # 自動判斷方向
    # 假設同一條路線的 stop_sequence 最小的是 go，最大的是 come
    def infer_direction(group):
        min_seq = group['stop_sequence'].min()
        max_seq = group['stop_sequence'].max()
        group['direction'] = group['stop_sequence'].apply(lambda x: 'go' if abs(x - min_seq) < abs(x - max_seq) else 'come')
        return group

    df = df.groupby(['route_id', 'route_name']).apply(infer_direction).reset_index(drop=True)

    # 重新排序
    df = df.sort_values(['route_id', 'direction', 'stop_sequence'])

    # 儲存為 utf-8-sig，避免 Excel 亂碼
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

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
            # 輸出即時動態CSV
            go_df.to_csv(f'./20250605/realtime_{selected["route_id"]}_go.csv', index=False, encoding='utf-8-sig')
            print(f"✅ 已輸出即時動態CSV：./20250605/realtime_{selected['route_id']}_go.csv")
        else:
            print("\n📍 即時動態（回程）：")
            print(back_df)
            # 輸出即時動態CSV
            back_df.to_csv(f'./20250605/realtime_{selected["route_id"]}_come.csv', index=False, encoding='utf-8-sig')
            print(f"✅ 已輸出即時動態CSV：./20250605/realtime_{selected['route_id']}_come.csv")

    # 嘗試用 utf-8-sig 或 big5 讀取，避免亂碼
    try:
        df = pd.read_csv("./20250605/full_route_stops.csv", encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv("./20250605/full_route_stops.csv", encoding="big5")

    # 去除重複資料
    df = df.drop_duplicates()

    # 自動判斷方向
    # 假設同一條路線的 stop_sequence 最小的是 go，最大的是 come
    def infer_direction(group):
        min_seq = group['stop_sequence'].min()
        max_seq = group['stop_sequence'].max()
        group['direction'] = group['stop_sequence'].apply(lambda x: 'go' if abs(x - min_seq) < abs(x - max_seq) else 'come')
        return group

    df = df.groupby(['route_id', 'route_name']).apply(infer_direction).reset_index(drop=True)

    # 重新排序
    df = df.sort_values(['route_id', 'direction', 'stop_sequence'])

    # 儲存為 utf-8-sig，避免 Excel 亂碼
    df.to_csv("./20250605/full_route_stops.csv", index=False, encoding="utf-8-sig")

    print("✅ full_route_stops.csv 已優化完成！")


