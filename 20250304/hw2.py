def gcd(a, b):
    # 基本情況：當 b 等於 0 時，返回 a，這時 a 就是最大公因數
    if b == 0:
        return a
    # 否則，遞迴呼叫 gcd(b, a % b)
    return gcd(b, a % b)

# 測試
result = gcd(11, 121)
print(result)  # 輸出應該是 11
def gcd(a, b):
    # 基本情況：當 b 等於 0 時，返回 a，這時 a 就是最大公因數
    if b == 0:
        return a
    # 否則，遞迴呼叫 gcd(b, a % b)
    return gcd(b, a % b)

# 測試
result = gcd(7, 49)
print('GCD is',result)  # 輸出應該是 7