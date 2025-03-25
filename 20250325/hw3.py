import requests
from bs4 import BeautifulSoup
import re

def get_bus_arrival_time(stop_name):
    url = 'https://pda5284.gov.taipei/MQS/route.jsp?rid=10417'
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    # 找到所有去程站名和到站時間的資料
    stops = soup.find_all('div', class_='stopName')
    times = soup.find_all('div', class_='eta')

    for stop, time in zip(stops, times):
        if stop_name in stop.text:
            # 使用正則表達式提取到站時間
            match = re.search(r'\d+', time.text)
            if match:
                return f"{stop_name} 站的公車將在 {match.group()} 分鐘後到達"
            else:
                return f"{stop_name} 站的公車即將到達"

    return f"找不到站名 {stop_name}"

if __name__ == "__main__":
    # 輸入站名
    stop_name = input("請輸入站名: ")
    arrival_time = get_bus_arrival_time(stop_name)
    print(arrival_time)
    