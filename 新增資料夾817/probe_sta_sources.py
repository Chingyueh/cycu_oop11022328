# probe_sta_sources.py  —— 穩健版：多種 $filter 語法自動降級，避免 400
import requests

CANDIDATES = [
    "https://sta.ci.taiwan.gov.tw/STA_Rain/v1.0",
    "https://sta.ci.taiwan.gov.tw/STA_River/v1.0",
    "https://sta.ci.taiwan.gov.tw/STA_Hydro/v1.0",
    # 其他你想測的可加在這裡
    "https://sta.ci.taiwan.gov.tw/STA_WaterLevel/v1.0",
    "https://sta.ci.taiwan.gov.tw/STA_Water/v1.0",
    "https://sta.ci.taiwan.gov.tw/STA_Discharge/v1.0",
    "https://sta.ci.taiwan.gov.tw/STA_Fhy/v1.0",
]

# 每個 metric 會用多種 $filter 語法嘗試（v4/v3 伺服器皆可）
KEYWORDS = {
    "rainfall": ["rain", "雨", "降雨", "rainfall", "precip"],
    "water_level": ["waterlevel", "water level", "stage", "水位"],
    "discharge": ["discharge", "flow", "流量", "m3/s", "cms", "cumec"],
}

# 不同伺服器對 OData 支援差異很大；這裡準備數種候選語法輪流嘗試
def filter_variants(kw: str):
    kw_lit = kw.replace("'", "''")  # 單引號 escape
    return [
        # OData v4 常見
        f"contains(tolower(name),'{kw_lit}')",
        f"contains(name,'{kw_lit}')",
        # 過濾 ObservedProperty（我們會加 $expand=ObservedProperty）
        f"contains(tolower(ObservedProperty/name),'{kw_lit}')",
        f"contains(ObservedProperty/name,'{kw_lit}')",
        # 一些實作仍支援的 v3 風格（substringof）
        f"substringof('{kw_lit}', tolower(name))",
        f"substringof('{kw_lit}', name)",
    ]

def endpoint_alive(base: str) -> bool:
    try:
        # 嘗試 $metadata 或 Things?$top=1，只要不是 404/410 就算活著
        r = requests.get(f"{base.rstrip('/')}/$metadata", timeout=10)
        if r.status_code in (404, 410):
            r = requests.get(f"{base.rstrip('/')}/Things", params={"$top": 1}, timeout=10)
        r.raise_for_status()
        return True
    except requests.RequestException:
        return False

def count_with_filter(base: str, f: str) -> int:
    url = f"{base.rstrip('/')}/Datastreams"
    params = {"$top": 100, "$skip": 0, "$expand": "ObservedProperty", "$filter": f}
    total = 0
    while True:
        r = requests.get(url, params=params, timeout=20)
        if r.status_code in (404, 410):
            # 此 endpoint 沒有 Datastreams 或路徑不同；視為 0
            return 0
        if r.status_code == 400:
            # 此語法不支援；交給呼叫端換下一種語法
            raise ValueError("bad filter syntax")
        r.raise_for_status()
        data = r.json()
        arr = data.get("value", [])
        total += len(arr)
        if len(arr) < params["$top"]:
            break
        params["$skip"] += params["$top"]
    return total

def count_metric(base: str, kw_list):
    """對同一 metric 輪流嘗試多個關鍵字 × 多種語法，回傳第一個 >0 的計數（或全部 0）"""
    for kw in kw_list:
        for f in filter_variants(kw):
            try:
                c = count_with_filter(base, f)
                if c > 0:
                    return c
            except ValueError:
                # 400 -> 換下一種寫法
                continue
            except requests.RequestException:
                # 網路或其他錯誤 -> 視為 0，換下一個
                continue
    return 0

def main():
    print("Probing SensorThings endpoints...")
    for base in CANDIDATES:
        if not endpoint_alive(base):
            print(f"❌ {base} -> not reachable")
            continue

        counts = {m: count_metric(base, kws) for m, kws in KEYWORDS.items()}
        if sum(counts.values()) == 0:
            print(f"⚠️ {base} -> reachable, but no matching Datastreams found")
        else:
            print(f"✅ {base}")
            for k, v in counts.items():
                print(f"   - {k}: {v}")

if __name__ == "__main__":
    main()
