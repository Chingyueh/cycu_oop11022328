# common.py  —— 與現有 schema 相容的完整工具集
import json
import sqlite3
import time
import requests
from datetime import datetime, timezone
from dateutil import tz
from dateutil.parser import isoparse
import backoff

from app_config import DB_PATH, TIMEZONE, METRIC_KEYWORDS

# 時區
LOCAL_TZ = tz.gettz(TIMEZONE)

# -----------------------------
# HTTP helpers
# -----------------------------
@backoff.on_exception(backoff.expo, (requests.RequestException,), max_tries=5)
def _get(url: str, params: dict | None = None) -> dict:
    """GET 並回傳 JSON；失敗自動退避重試。"""
    r = requests.get(url, params=params or {}, timeout=20)
    r.raise_for_status()
    return r.json()

def fetch_paged(url: str, params: dict | None = None, page_size: int = 1000):
    """
    SensorThings API 以 $top + $skip 分頁。
    - 若遇到 404/410，視為該端點不存在，直接停止這個來源的分頁（交由上層嘗試其他 BASE_URL）。
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
                return  # 結束這個來源
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
    """建立 SQLite 連線，採 WAL + NORMAL 提昇穩定性。"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

# -----------------------------
# Metric classification
# -----------------------------
def classify_metric(ds_name: str) -> str:
    """
    簡單版：只依 Datastream.name 文字比對。
    （保留給部分腳本使用；主要仍建議用下方的 classify_metric_from_ds）
    """
    n = (ds_name or "").lower()
    for m, keys in METRIC_KEYWORDS.items():
        for k in keys:
            if k in n:
                return m
    return ""

# 強化版：接受「整個 Datastream dict」，綜合多欄位判斷
DEBUG_METRIC_SAMPLE = 10  # >0 會印出最多 N 筆未分類樣本；部署後可改 0 關閉
_debug_counter = {"printed": 0}

def _safe_lower(s):
    return (s or "").strip().lower()

def classify_metric_from_ds(ds: dict) -> str:
    """
    回傳 'rainfall' / 'water_level' / 'discharge' 或 ''（不確定）
    參考欄位：
      - ds.name / ds.description
      - ds.ObservedProperty.name / .description
      - ds.unitOfMeasurement.name / .symbol
      - ds.Thing.name
    """
    # 收集可用文字
    name_desc = " ".join([_safe_lower(ds.get("name")), _safe_lower(ds.get("description"))])

    op = ds.get("ObservedProperty") or {}
    op_name_desc = " ".join([_safe_lower(op.get("name")), _safe_lower(op.get("description"))])

    unit = ds.get("unitOfMeasurement") or {}
    unit_text = " ".join([_safe_lower(unit.get("name")), _safe_lower(unit.get("symbol"))])

    thing = ds.get("Thing") or {}
    thing_text = _safe_lower(thing.get("name"))

    haystack = " ".join([name_desc, op_name_desc, unit_text, thing_text])

    # 關鍵字盡量涵蓋中英文與常見單位標示
    keys = {
        "rainfall": [
            "rain", "rainfall", "precip", "rr", "rain rate",
            "降雨", "雨量", "時雨量", "小時雨量", "十分鐘雨量", "10分鐘雨量", "累積雨量",
            "mm/hr", "mmh", "毫米", "mm"
        ],
        "water_level": [
            "waterlevel", "water level", "stage", "river level",
            "水位", "河川水位", "警戒水位", "基準水位",
            "水位(m)", "level(m)", "公尺", "meter", "m"
        ],
        "discharge": [
            "discharge", "flow", "river flow",
            "流量", "河川流量",
            "cms", "cumec", "m3/s", "m³/s", "立方公尺每秒", "cms(m3/s)"
        ],
    }

    for metric, kwlist in keys.items():
        for kw in kwlist:
            if kw in haystack:
                return metric

    # 以單位推斷（保守）
    if any(u in unit_text for u in ["m3/s", "m³/s", "cms", "cumec", "立方公尺每秒"]):
        return "discharge"
    if any(u in unit_text for u in ["水位(m)", "level(m)", "公尺", "meter"]) or unit_text.strip() == "m":
        if not any(k in haystack for k in keys["rainfall"]):
            return "water_level"

    # 未分類樣本（協助之後微調關鍵字）
    if DEBUG_METRIC_SAMPLE and _debug_counter["printed"] < DEBUG_METRIC_SAMPLE:
        _debug_counter["printed"] += 1
        print("❓ Unclassified DS sample:",
              "ds_id=", ds.get("@iot.id"),
              "| name=", ds.get("name"),
              "| ObservedProperty.name=", (op.get("name") if op else None),
              "| unit=", unit.get("name") if unit else None, "/", unit.get("symbol") if unit else None,
              "| thing=", thing.get("name") if thing else None)
    return ""

# -----------------------------
# Time helpers
# -----------------------------
def to_utc_dt(iso_str: str) -> datetime:
    """將 ISO 時間字串轉為 UTC aware datetime。若無時區，視為 UTC。"""
    dt = isoparse(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def to_local_iso(dt_utc: datetime) -> str:
    """將 UTC datetime 轉成本地時區的 ISO 字串（秒精度）。"""
    return dt_utc.astimezone(LOCAL_TZ).replace(microsecond=0).isoformat()
