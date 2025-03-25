import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.sans-serif']=[ 'microsoft JhengHei']
import pandas as pd
import matplotlib.pyplot as plt

def plot_cash_exchange_rate(file_path):
    try:
        # 讀取 Excel 檔案
        df = pd.read_excel(file_path, engine='openpyxl')

        # 列出欄位名稱以供檢查
        print("Excel 檔案中的欄位名稱：", df.columns)

        # 去除欄位名稱的多餘空格
        df.columns = df.columns.str.strip()

        # 檢查必要欄位是否存在
        required_columns = ['資料日期', '本行買入現金', '本行賣出現金']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"缺少必要欄位: {col}")

        # 過濾出日期格式的資料
        df = df[df['資料日期'].astype(str).str.match(r'^\d{8}$', na=False)]

        # 將資料日期轉換為日期格式
        df['資料日期'] = pd.to_datetime(df['資料日期'], format='%Y%m%d')

        # 檢查是否有空值
        print("是否有空值：")
        print(df[['本行買入現金', '本行賣出現金']].isnull().sum())

        # 移除空值
        df = df.dropna(subset=['本行買入現金', '本行賣出現金'])

        # 確保數據為數值型態
        df['本行買入現金'] = pd.to_numeric(df['本行買入現金'], errors='coerce')
        df['本行賣出現金'] = pd.to_numeric(df['本行賣出現金'], errors='coerce')

        # 檢查處理後的數據
        print("處理後的數據：")
        print(df[['資料日期', '本行買入現金', '本行賣出現金']].head())

        # 繪製圖表
        plt.figure(figsize=(10, 6))
        plt.plot(df['資料日期'], df['本行買入現金'], label='本期買入現金', marker='o', color='blue')
        plt.plot(df['資料日期'], df['本行賣出現金'], label='本期賣出現金', marker='o', color='red')

        # 設定圖表標題與標籤
        plt.title('每日現金買入與賣出匯率', fontsize=16)
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('匯率', fontsize=12)
        plt.legend()
        plt.grid()
        plt.xticks(rotation=45)

        # 顯示圖表
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"處理資料時發生錯誤: {e}")

if __name__ == "__main__":
    # 使用原始字串格式避免路徑問題
    excel_file_path = r"C:\Users\User\Desktop\cycu_oop11022328\20250325\0325.xlsx"
    plot_cash_exchange_rate(excel_file_path)