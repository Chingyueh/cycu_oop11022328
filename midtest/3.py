import requests
import pandas as pd

def fetch_bus_route_data(bus_code):
    # 定義 URL，並帶入公車代碼
    url = f'https://ebus.gov.taipei/Route/StopsOfRoute?routeid={bus_code}'

    # 向網站發送 GET 請求，取得 JSON 資料
    response = requests.get(url)
    
    # 檢查回應狀態碼
    if response.status_code != 200:
        print(f"Error: Unable to fetch data. Status code {response.status_code}")
        return

    # 解析 JSON 資料
    data = response.json()

    # 檢查是否包含 'arrival_info' 資料
    if 'arrival_info' not in data:
        print("Error: No 'arrival_info' found in the data.")
        return

    # 解析 'arrival_info' 部分資料
    arrival_info = data['arrival_info']

    # 儲存需要的資料
    rows = []
    for stop in arrival_info:
        stop_number = stop.get('stop_number', '')
        stop_name = stop.get('stop_name', '')
        stop_id = stop.get('stop_id', '')
        latitude = stop.get('latitude', '')
        longitude = stop.get('longitude', '')
        arrival_time = stop.get('arrival_time', '')

        # 將每一條資料作為一行添加到列表中
        rows.append([arrival_time, stop_number, stop_name, stop_id, latitude, longitude])

    # 將資料轉換為 DataFrame
    df = pd.DataFrame(rows, columns=["公車到達時間", "車站序號", "車站名稱", "車站編號", "經緯度座標 latitude", "longitude"])

    # 輸出為 CSV 檔案
    df.to_csv(f"bus_route_{bus_code}.csv", index=False, encoding='utf-8')
    print(f"CSV file 'bus_route_{bus_code}.csv' has been saved.")

if __name__ == "__main__":
    # 請求用戶輸入公車代碼
    bus_code = input("請輸入公車代碼（例如：0100000A00）：")
    
    # 執行函數抓取並處理資料
    fetch_bus_route_data(bus_code)

