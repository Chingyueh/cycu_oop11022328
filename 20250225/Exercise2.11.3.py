#part1
# 定義半徑（單位為厘米）
radius = 5  # 半徑為 5 厘米

# 計算球體的體積，公式是 (4/3) * π * r^3
import math  # 引入數學模塊，以便使用 π

volume = (4/3) * math.pi * radius**3  # 體積計算，單位是立方厘米

# 顯示結果
print("part1 volume=", volume, "立方厘米")  # 顯示體積（立方厘米）

#part2
x=42
v=math.sin(x) ** 2 + math.cos(x) **2
print('part2=',v)
#part3
print('math.e',math.e)
print('math.e**2',math.e**2)
print('math.exp(2)',math.exp(2))