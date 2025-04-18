import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

def plot_normal_distribution():
    # 請用戶輸入均值 μ 和標準差 σ
    mu = float(input("請輸入均值 μ: "))
    sigma = float(input("請輸入標準差 σ: "))

    # 生成數據
    x = np.linspace(mu - 4*sigma, mu + 4*sigma, 1000)  # 設定顯示範圍
    y = norm.pdf(x, mu, sigma)  # 計算對應的機率密度

    # 繪圖
    plt.figure(figsize=(8, 6))
    plt.plot(x, y, label=f'Normal Distribution\n$\mu={mu}, \sigma={sigma}$', color='b')
    plt.title(f'Normal Distribution: $\mu={mu}$, $\sigma={sigma}$')
    plt.xlabel('x')
    plt.ylabel('Probability Density')
    plt.grid(True)
    plt.legend(loc='best')

    # 儲存為 JPG 文件，檔名為 "normal_pdf_μ_σ.jpg"
    filename = f"normal_pdf_{mu}_{sigma}.jpg"
    plt.savefig(filename, format='jpg')
    plt.close()
    print(f"圖表已儲存為 {filename}")

# 執行函數
plot_normal_distribution()
