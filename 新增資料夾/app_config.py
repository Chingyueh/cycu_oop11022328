# app_config.py
# 支援多個 Civil IoT 的 SensorThings 入口。若其中某些庫不存在，程式會自動略過（404/410 被處理）。

BASE_URLS = [
    # 官方建議的分流主機
    "https://sta.colife.org.tw/STA_Rain/v1.0",             # 雨量
    "https://sta.colife.org.tw/STA_WaterResource_v2/v1.0"  # 水資源：含水位/流量/地下水位/淹水等
]

DB_PATH = "hydro.db"
OUTPUT_DIR = "output/hourly"
TIMEZONE = "Asia/Taipei"

# 指標關鍵字（用於簡單分類；強化版則在 common.classify_metric_from_ds）
METRIC_KEYWORDS = {
    "rainfall": [
        "rain", "rainfall", "precip",
        "降雨", "雨量", "小時雨量", "累積雨量"
    ],
    "water_level": [
        "waterlevel", "water level", "stage",
        "水位", "河川水位", "地下水位", "水深", "淹水深度"
    ],
    "discharge": [
        "discharge", "flow",
        "流量", "河川流量", "累計流量",
        "m3/s", "cms", "cumec"
    ],
}

# 從 API 抓「最近這麼多分鐘」的觀測，寫入 DB
WINDOW_MIN = 20
# 產出小時 CSV 時是否補滿 6 個 10 分鐘格（沒資料的留空）
FILL_MISSING_GRID = True
