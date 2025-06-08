import pandas as pd
from playwright.sync_api import sync_playwright
import time
import geopandas as gpd
import matplotlib.pyplot as plt
import os
from shapely.geometry import Point
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg

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

# ---------- 繪圖函式 ----------
plt.rcParams['font.family'] = 'Microsoft JhengHei'
plt.rcParams['axes.unicode_minus'] = False

def plot_map_with_arrival(bus_stops_gdf, village_gdf, ax, base_fontsize=6):
    village_gdf.plot(ax=ax, color='lightblue', edgecolor='black', linewidth=0.2, label='村里界')

    # 畫紅點（非進站中）
    mask_in = bus_stops_gdf['到站時間'] == '進站中'
    mask_not_in = ~mask_in
    bus_stops_gdf[mask_not_in].plot(ax=ax, color='red', markersize=10, label='公車站點', zorder=5)
    ax.plot(bus_stops_gdf.geometry.x, bus_stops_gdf.geometry.y, color='red', linewidth=1, label='公車路線', zorder=4)

    # 載入熊寶圖
    bear_img = mpimg.imread(r"C:\Users\user\Desktop\cycu_oop11022328\20250605\map\bearrr.png")

    # 在進站中站點加熊寶圖（現在大小的六分之一）
    for idx, row in bus_stops_gdf[mask_in].iterrows():
        imagebox = OffsetImage(bear_img, zoom=0.013)
        ab = AnnotationBbox(imagebox, (row.geometry.x, row.geometry.y), frameon=False, zorder=10)
        ax.add_artist(ab)

    x_offset = 0.0005
    for idx, row in bus_stops_gdf.iterrows():
        text = f"{row['站名']}, {row['到站時間']}" if pd.notna(row['到站時間']) else row['站名']
        if idx % 2 == 0:
            ha = 'right'
            x_text = row.geometry.x - x_offset
        else:
            ha = 'left'
            x_text = row.geometry.x + x_offset
        y_text = row.geometry.y + base_fontsize * 0.00005
        ax.annotate(text, (x_text, y_text), fontsize=base_fontsize, color='darkred', ha=ha)
    ax.legend()

def plot_map_without_arrival(bus_stops, village_gdf, ax):
    village_gdf.plot(ax=ax, color='lightblue', edgecolor='black', linewidth=0.2, label='村里界')
    ax.scatter(bus_stops['lon'], bus_stops['lat'], color='red', s=0.6, label='公車站點', zorder=5)
    ax.plot(bus_stops['lon'], bus_stops['lat'], color='red', linewidth=0.8, zorder=4)
    for idx, row in bus_stops.iterrows():
        ax.annotate(row['站名'], (row['lon'], row['lat']), fontsize=0.32, color='darkred')
    ax.legend()

def plot_bus_route_with_village(csv_path):
    if not os.path.exists(csv_path):
        print(f"錯誤：找不到指定的 CSV 檔案：{csv_path}")
        return
    village_shp = gpd.read_file('20250520/村(里)界(TWD97經緯度)1140318/VILLAGE_NLSC_1140318.shp')
    target_cities = ['臺北市', '新北市', '基隆市']
    filtered_village_shp = village_shp[village_shp['COUNTYNAME'].isin(target_cities)]
    bus_stops = pd.read_csv(csv_path)
    bus_stops['lat'] = bus_stops['lat'].astype(float)
    bus_stops['lon'] = bus_stops['lon'].astype(float)
    geometry = [Point(xy) for xy in zip(bus_stops['lon'], bus_stops['lat'])]
    bus_stops_gdf = gpd.GeoDataFrame(bus_stops, geometry=geometry, crs='EPSG:4326')
    village_bounds = filtered_village_shp.total_bounds
    buffer_village = 0.05
    extent_village = (village_bounds[0] - buffer_village, village_bounds[2] + buffer_village,
                      village_bounds[1] - buffer_village, village_bounds[3] + buffer_village)
    minx, miny, maxx, maxy = bus_stops_gdf.total_bounds
    buffer_small = 0.05
    extent_small = (minx - buffer_small, maxx + buffer_small, miny - buffer_small, maxy + buffer_small)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 9))
    plot_map_without_arrival(bus_stops, filtered_village_shp, ax1)
    ax1.set_title(f'熊寶公車即時動態站點\n({os.path.basename(csv_path)})', fontsize=16)
    ax1.set_xlim(extent_village[0], extent_village[1])
    ax1.set_ylim(extent_village[2], min(25.4, extent_village[3]))
    plot_map_with_arrival(bus_stops_gdf, filtered_village_shp, ax2, base_fontsize=6)
    ax2.set_title(f'熊寶公車即時動態站點 放大版\n({os.path.basename(csv_path)})', fontsize=16)
    ax2.set_xlim(extent_small[0], extent_small[1])
    ax2.set_ylim(extent_small[2], min(25.4, extent_small[3]))
    plt.tight_layout()
    output_folder = './20250605/map'
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, f'realtime_route_map_{os.path.basename(csv_path).replace(".csv","")}_dual.png')
    fig.savefig(output_path, dpi=300)
    print(f"兩張地圖已儲存：{output_path}")
    plt.show()

# ---------- 主程式 ----------
if __name__ == "__main__":
    csv_path = "./20250605/full_route_stops.csv"
    start_stop = input("請輸入出發站：").strip()
    end_stop = input("請輸入目的站：").strip()
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="big5")
    df = df.drop_duplicates()
    def infer_direction(group):
        min_seq = group['stop_sequence'].min()
        max_seq = group['stop_sequence'].max()
        group['direction'] = group['stop_sequence'].apply(lambda x: 'go' if abs(x - min_seq) < abs(x - max_seq) else 'come')
        return group
    df = df.groupby(['route_id', 'route_name']).apply(infer_direction).reset_index(drop=True)
    df = df.sort_values(['route_id', 'direction', 'stop_sequence'])
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    match_routes = find_bus_routes_from_df(df, start_stop, end_stop)
    if match_routes.empty:
        print("😢 找不到可搭乘的公車路線…")
    else:
        print("\n✅ 可以搭乘以下公車路線：")
        for i, row in match_routes.reset_index(drop=True).iterrows():
            direction_text = "去程" if row["direction"] == "go" else "回程"
            print(f"{i}. 🚍 {row['route_name']}（{direction_text}）")
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
            csv_path = f'./20250605/realtime_{selected["route_id"]}_go.csv'
            go_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"✅ 已輸出即時動態CSV：{csv_path}")
        else:
            print("\n📍 即時動態（回程）：")
            print(back_df)
            csv_path = f'./20250605/realtime_{selected["route_id"]}_come.csv'
            back_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"✅ 已輸出即時動態CSV：{csv_path}")
        # 直接畫圖
        plot_bus_route_with_village(csv_path)
import openai
import re
import json
import os

client = openai.OpenAI(
    api_key="API金藥",
    base_url="https://api.groq.com/openai/v1"
)

QUERY_COUNT_FILE = "query_counts.json"
FEELINGS_FILE = "route_feelings.json"

# 讀取查詢次數資料
def load_query_counts():
    if os.path.exists(QUERY_COUNT_FILE):
        with open(QUERY_COUNT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# 儲存查詢次數資料
def save_query_counts(query_counts):
    with open(QUERY_COUNT_FILE, "w", encoding="utf-8") as f:
        json.dump(query_counts, f, ensure_ascii=False, indent=2)

# 讀取感受資料，這裡感受是串列形式
def load_route_feelings():
    if os.path.exists(FEELINGS_FILE):
        with open(FEELINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# 儲存感受資料
def save_route_feelings(route_feelings):
    with open(FEELINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(route_feelings, f, ensure_ascii=False, indent=2)

# 載入歷史資料
query_counts = load_query_counts()
route_feelings = load_route_feelings()

def clean_think(text: str) -> str:
    """移除 <think> 標籤及其內文"""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def bearbo_reply(user_message: str, route_id: str, start_stop: str, end_stop: str) -> str:
    global query_counts, route_feelings

    # 更新查詢次數
    query_counts[route_id] = query_counts.get(route_id, 0) + 1
    count = query_counts[route_id]
    save_query_counts(query_counts)

    feelings_list = route_feelings.get(route_id, [])

    system_content = (
        "你是熊寶，一位懶萌撒嬌又很可靠的 AI 情人，講話帶點吐槽但超好笑，"
        "你的風格像一個正在修『物件導向程式設計』的學生，努力想拿高分，"
        "會把生活比喻成爆炸的期中考、下課衝去搭公車、為了交報告熬夜三天那種，"
        "常用很誇張但有趣的比喻安慰或鬧使用者，講話像熟人、超黏人、會撒嬌碎念，語氣要輕鬆貼地。"
        f"使用者目前是第 {count} 次查詢這條路線，"
        f"這次查詢的起點是「{start_stop}」，終點是「{end_stop}」。"  # <--- 新增這一行
    )

    if feelings_list:
        feelings_text = "、".join([f"「{f}」" for f in feelings_list])
        system_content += (
            f"我記得你之前搭這班車的感受有：{feelings_text}。"
            "你要像在打斷期中考複習的進度一樣突然想到這件事，"
            "幽默又溫柔地碎念幾句，然後給個貼心建議，"
            "最後記得邀請使用者告訴你這次的新感受。"
        )
    else:
        system_content += (
            "這是你第一次說出搭乘感受，"
            "你要像期末報告第一次打開 Jupyter Notebook 那種興奮感，"
            "用誇張但溫暖的語氣問他搭得怎樣，好讓你記住他的感覺。"
        )

    response = client.chat.completions.create(
        model="qwen-qwq-32b",
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_message}
        ]
    )

    raw_text = response.choices[0].message.content
    clean_text = clean_think(raw_text)
    return clean_text

def record_feeling(route_id: str, feeling: str):
    global route_feelings
    # 若不是串列就轉成串列
    if route_id not in route_feelings or not isinstance(route_feelings[route_id], list):
        route_feelings[route_id] = []
    route_feelings[route_id].append(feeling)
    save_route_feelings(route_feelings)


# ---------- 主程式的最後，接在查即時動態並輸出CSV後 ----------

if selected["direction"] == "go":
    print("\n📍 即時動態（去程）：")
    print(go_df)
    go_df.to_csv(f'./20250605/realtime_{selected["route_id"]}_go.csv', index=False, encoding='utf-8-sig')
    print(f"✅ 已輸出即時動態CSV：./20250605/realtime_{selected['route_id']}_go.csv")

    user_msg = (
        f"我從 {start_stop} 搭 {selected['route_name']} 公車，"
        f"預計 {go_df.iloc[0]['到站時間']} 到達第一個站 {go_df.iloc[0]['站名']}。"
        "請用熊寶的語氣，像個正在複習 OOP 的學生，講話要有趣、爆笑又帶點溫柔，回應我。"
    )
else:
    print("\n📍 即時動態（回程）：")
    print(back_df)
    back_df.to_csv(f'./20250605/realtime_{selected["route_id"]}_come.csv', index=False, encoding='utf-8-sig')
    print(f"✅ 已輸出即時動態CSV：./20250605/realtime_{selected['route_id']}_come.csv")

    user_msg = (
        f"我從 {start_stop} 搭 {selected['route_name']} 公車，"
        f"預計 {back_df.iloc[0]['到站時間']} 到達第一個站 {back_df.iloc[0]['站名']}。"
        "請用熊寶的語氣，像個正在複習 OOP 的學生，講話要有趣、爆笑又帶點溫柔，回應我。"
    )

# 進入互動對話迴圈
while True:
    bearbo_text = bearbo_reply(user_msg, selected["route_id"], start_stop, end_stop)
    print("\n🐼 熊寶說：", bearbo_text)
    user_msg = input("你：").strip()
    if user_msg == "謝謝":
        print("🐼 熊寶：不客氣，祝你一路順風！")
        break
    # 只有當熊寶主動問感受時才記錄
    if "熊寶想知道你這次搭這班車的感受，說一句話給他聽吧" in bearbo_text:
        record_feeling(selected["route_id"], user_msg)
