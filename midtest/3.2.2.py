import asyncio
import csv
import json
import os
from playwright.async_api import async_playwright

async def fetch_bus_data(bus_code):
    api_url = f"https://ebus.gov.taipei/Route/StopsOfRoute?routeid={bus_code}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 🧠 用 Playwright 模擬瀏覽器去發送 API 請求
        response = await page.request.get(api_url)
        if response.status != 200:
            print(f"❌ 請求失敗，HTTP 狀態碼：{response.status}")
            await browser.close()
            return

        try:
            data = await response.json()
        except Exception as e:
            print("❌ JSON 解析錯誤：", e)
            content = await response.text()
            print("原始內容：", content[:200])
            await browser.close()
            return

        print(f"✅ 成功取得資料，共 {len(data)} 筆")

        # 資料轉換
        extracted = []
        for stop in data:
            arrival_info = stop.get("arrival", {}).get("estimate_time", "N/A")
            stop_number = stop.get("stop_order", "N/A")
            stop_name = stop.get("stop_name", {}).get("zh_tw", "N/A")
            stop_id = stop.get("stop_id", "N/A")
            latitude = stop.get("position", {}).get("lat", "N/A")
            longitude = stop.get("position", {}).get("lng", "N/A")
            extracted.append([arrival_info, stop_number, stop_name, stop_id, latitude, longitude])

        # 輸出為 CSV
        save_path = os.path.abspath("bus_stops.csv")
        with open(save_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["公車到達時間", "車站序號", "車站名稱", "車站編號", "latitude", "longitude"])
            writer.writerows(extracted)

        print(f"✅ 資料已儲存為 CSV：{save_path}")
        await browser.close()

if __name__ == "__main__":
    bus_code = input("請輸入公車代碼（例如 0100000A00）：")
    asyncio.run(fetch_bus_data(bus_code))
