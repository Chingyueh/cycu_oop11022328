import os
import pandas as pd

def read_and_sum_excel(file_path):
    if not os.path.exists(file_path):
        print(f"檔案 {file_path} 不存在")
        return
    
    # 讀取 Excel 檔案
    df = pd.read_excel(file_path)
    
    # 假設欄位名稱為 'x' 和 'y'
    df['sum'] = df['x'] + df['y']
    
    # 印出結果
    print(df)

if __name__ == '__main__': 
    file_path = 'C:\\Users\\User\\Desktop\\cycu_oop11022328\\20250311\\11022328.xlsx'  # 替換為你的 Excel 檔案路徑
    read_and_sum_excel(file_path)