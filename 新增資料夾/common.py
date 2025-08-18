# common.py  —— 可直接覆蓋
import json
import sqlite3
from typing import Generator
from datetime import datetime, timezone

import backoff
import requests
from dateutil import tz
from dateutil.parser import isoparse

# 只從設定拿 DB 路徑與時區（避免循環引用）
from app_config import DB_PATH, TIMEZONE

# 本地時區
LOCAL_TZ = tz.gettz(TIMEZONE)


# -----------------------------
# HTTP helpers
# -----------------------------
@backoff.on_exception(backoff.expo, (requests.RequestException,), max_tries=5)
def _get(url: str, params: dict | None = None) -> dict:
    r = requests.get(url, params=params or {}, timeout=20)
    r.raise_for_status()
    return r.json()


def fetch_paged(url: str, params: dict | None = None, page_size: int = 1000) -> Generator[dict, None, None]:
    """
    SensorThings API 以 $top + $skip 分頁。
    遇到 404/410 視為該端點不存在，結束這個來源的分頁。
    """
    params = dict(params or {})
    params.setdefault("$top", page_size)
    skip = 0
    while True:
        params["$skip"] = skip
        try:
            data = _get(url, params)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (404, 410):
                return
            raise
        values = data.get("value", [])
        if not values:
            break
        for v in values:
            yield v
        if len(values) < page_size:
            break
        skip += page_size


# -----------------------------
# DB helper
# -----------------------------
def ensure_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


# -----------------------------
# Time helpers
# -----------------------------
def to_utc_dt(iso_str: str) -> datetime:
    """將 ISO 字串轉成 UTC aware datetime；若無時區視為 UTC。"""
    dt = isoparse(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_local_iso(dt_utc: datetime) -> str:
    """UTC datetime → 本地時區 ISO（秒精度）。"""
    return dt_utc.astimezone(LOCAL_TZ).replace(microsecond=0).isoformat()


# -----------------------------
# Metric classifier（強化版）
# -----------------------------
def classify_metric_from_ds(ds: dict) -> str:
    """
    依下列優先序決定 metric：
    1) 讀 description 中的 Datastream_Category_type：
       - 河川水位站 → river_water_level
       - 地下水位站 → groundwater_level
       - 區域排水水位站 → drainage_water_level
       - 雨量感測器 → rainfall
       - 流量感測器 → discharge / discharge_cum (看是否為累積)
    2) 後備：用 name/description/ObservedProperty/unit 之關鍵字推論
    回傳其中之一：
      rainfall / river_water_level / groundwater_level / drainage_water_level / discharge / discharge_cum
    若無法判斷，回傳空字串 ""（之後會被略過）。
    """
    name = (ds.get("name") or "")
    desc = (ds.get("description") or "")
    op = (ds.get("ObservedProperty") or {})
    op_name = (op.get("name") or "")
    unit = (ds.get("unitOfMeasurement") or {})
    unit_name = (unit.get("name") or "")
    unit_sym = (unit.get("symbol") or "")

    # ---- 1) description 中的 Datastream_Category_type ----
    # 不區分大小寫，同時比對中文
    desc_l = desc.lower()

    # 水位三類
    if ("Datastream_Category_type=河川水位站" in desc) or ("河川水位站" in desc):
        return "river_water_level"
    if ("Datastream_Category_type=地下水位站" in desc) or ("地下水位站" in desc):
        return "groundwater_level"
    if ("Datastream_Category_type=區域排水水位站" in desc) or ("區域排水水位站" in desc):
        return "drainage_water_level"

    # 雨量
    if ("Datastream_Category_type=雨量感測器" in desc) or ("雨量感測器" in desc):
        return "rainfall"

    # 流量（累積 or 即時）
    if ("Datastream_Category_type=流量感測器" in desc) or ("流量感測器" in desc):
        # 累積關鍵字
        if any(k in (name + op_name + desc) for k in ["累計", "累積", "accum", "cumulative", "total"]):
            return "discharge_cum"
        return "discharge"

    # ---- 2) 後備：綜合 name/ObservedProperty/unit 關鍵字 ----
    hay = f"{name} {desc} {op_name} {unit_name} {unit_sym}".lower()

    # Rainfall
    rain_kw = ["rain", "rainfall", "precip", "降雨", "雨量"]
    if any(k in hay for k in rain_kw):
        return "rainfall"

    # Flow / Discharge
    flow_kw = ["discharge", "flow", "流量", "cms", "m3/s", "cumec"]
    if any(k in hay for k in ["accum", "cumulative", "total", "累計", "累積"]) and any(k in hay for k in flow_kw):
        return "discharge_cum"
    if any(k in hay for k in flow_kw):
        return "discharge"

    # Water level（無法區分時給一般 water_level，讓你看得出來還有未歸類者）
    wl_kw = ["waterlevel", "water level", "stage", "水位"]
    if any(k in hay for k in wl_kw):
        # 嘗試從字串細分
        if "河川" in (name + desc):
            return "river_water_level"
        if "地下" in (name + desc):
            return "groundwater_level"
        if "區域排水" in (name + desc) or "排水" in (name + desc):
            return "drainage_water_level"
        # 退而求其次：一般水位（若你不想要 generic，可改成空字串）
        return "river_water_level"  # 多數資料為河川水位；若偏好 generic：return "water_level"

    return ""
