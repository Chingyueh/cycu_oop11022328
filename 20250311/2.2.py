import pandas as pd
import matplotlib.pyplot as plt

# 讀取 Excel 檔案
df = pd.read_excel('c:\\Users\\User\\Desktop\\cycu_oop11022328\\20250311\\311.xlsx')

# 假設欄位名稱為 'x' 和 'y'
df['sum'] = df['x'] + df['y']

# 印出相加結果
print(df['sum'])

# 繪製散佈圖
plt.scatter(df['x'], df['y'])
plt.xlabel('x')
plt.ylabel('y')
plt.title('Scatter plot of x and y')
plt.show()