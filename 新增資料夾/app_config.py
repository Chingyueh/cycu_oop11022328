# app_config.py
# — 多入口（建議使用 colife 分流）
BASE_URLS = [
    "https://sta.colife.org.tw/STA_Rain/v1.0",
    "https://sta.colife.org.tw/STA_WaterResource_v2/v1.0",
]

# SQLite 檔案
DB_PATH = "hydro.db"

# 每個變數輸出到：OUTPUT_ROOT/<metric>/hourly/YYYY/MM/DD/HH.csv
OUTPUT_ROOT = "output"

# 本地時區（影響 CSV hour 與 sample_time）
TIMEZONE = "Asia/Taipei"

# 近幾分鐘視窗（抓 Observation），交由 DB 主鍵去重
WINDOW_MIN = 20

# 小時 CSV 是否補滿六個 10 分鐘格（缺值留空）
FILL_MISSING_GRID = True

# （可選）權責單位過濾：只輸出屬於以下單位的測站（留空 [] = 不過濾）
# 例：["水利署", "水利署（與縣市政府合建）"]
ALLOW_AUTHORITIES = []

# （推薦）程式端白名單：依 Datastream.description 內容過濾（不改抓取流程也能精準輸出）
# 完全等價你貼的五大類：
CATEGORY_WHITELIST_SUBSTR = [
    # "Datastream_Category_type=河川水位站",
    # "Datastream_Category_type=地下水位站",
    # "Datastream_Category_type=雨量感測器",
    # "Datastream_Category_type=流量感測器",
    # "Datastream_Category_type=區域排水水位站",
]

# =========================
# 下面是「可選的」API 端過濾開關
# =========================
# 打開後，sync_catalog 抓 Datastreams 時，會把上面的白名單條件下推到 API 的 $filter
API_FILTER_ENABLED = False  # ← 需要降載時才改 True

# （可選）在 API 端同時加權責單位過濾（只在 API_FILTER_ENABLED=True 時作用）
API_FILTER_AUTHORITIES = []  # 例：["水利署", "水利署（與縣市政府合建）"]

# 備用：舊版簡單關鍵字（強化分類已在 common.classify_metric_from_ds）
METRIC_KEYWORDS = {
    "rainfall": ["rain", "rainfall", "precip", "降雨", "雨量", "小時雨量", "累積雨量", "past10min", "past1hr", "past24hr"],
    "water_level": ["waterlevel", "water level", "stage", "水位", "河川水位", "地下水位", "水深", "淹水深度"],
    "discharge": ["discharge", "flow", "流量", "河川流量", "m3/s", "m³/s", "cms", "cumec", "立方公尺每秒"],
    "discharge_cum": ["累計流量", "累積流量", "cumulative flow", "total flow", "m3", "立方公尺"],
}
