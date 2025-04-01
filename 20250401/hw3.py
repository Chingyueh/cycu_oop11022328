import os
import pandas as pd
from bs4 import BeautifulSoup

# 使用 os.path 處理路徑
html_file = os.path.join(
    r'c:/Users/User/Downloads/cycu_oop11022328/20250401',
    '[忠孝幹線(公車雙向轉乘優惠)]公車動態資訊.html'
)

# 確保檔案存在
if not os.path.exists(html_file):
    raise FileNotFoundError(f"檔案不存在：{html_file}")

# 讀取 HTML 檔案
with open(html_file, 'r', encoding='utf-8') as file:
    soup = BeautifulSoup(file, 'html.parser')

# 初始化資料列表
data = []

# 找到所有符合條件的 tr 標籤
for tr in soup.find_all("tr", class_=["ttego1", "ttego2", "tteback1", "tteback2"]):
    # 提取站點名稱
    td_name = tr.find("td")
    stop_name = td_name.text.strip() if td_name else "未知"

    # 提取站點連結
    stop_link = td_name.find("a")["href"] if td_name and td_name.find("a") else "無連結"

    # 提取到站時間
    td_time = tr.find_all("td")[-1]  # 通常到站時間在最後一個 <td>
    arrival_time = td_time.text.strip() if td_time else "未知"

    # 將資料加入列表
    data.append({"站點名稱": stop_name, "連結": stop_link, "到站時間": arrival_time})

# 將資料轉換為 Pandas DataFrame
df = pd.DataFrame(data)

# 顯示結果
print(df)

# 確保輸出目錄存在
output_dir = r'c:/Users/User/Downloads/cycu_oop11022328/20250401'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 儲存結果為 CSV 檔案
output_file = os.path.join(output_dir, 'bus_dynamic_info.csv')
df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"動態到站資訊已儲存至 {output_file}")