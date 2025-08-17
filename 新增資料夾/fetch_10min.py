# fetch_10min.py —— 先同步 stations/datastreams，再抓近 WINDOW_MIN 分鐘觀測（支援 雨量/水位/流量）
import json, requests
from datetime import datetime, timedelta, timezone

from common import (
    ensure_conn,
    fetch_paged,
    _get,
    to_utc_dt,
    classify_metric_from_ds,   # 加強版分類（綜合 name/ObservedProperty/unit）
)
from app_config import BASE_URLS, WINDOW_MIN


def iter_sources(path_suffix: str):
    for base in BASE_URLS:
        yield base, f"{base.rstrip('/')}/{path_suffix.lstrip('/')}"


THINGS_PATH = "Things"


def sync_catalog(conn):
    """
    同步 stations / datastreams 進 DB。
    這裡走「逐站 → 取 Datastreams（展開 ObservedProperty）」的保守路徑，以相容各庫端點。
    若覺得太慢，可以再換成「直接掃 /Datastreams?$expand=Thing,ObservedProperty」的快速版。
    """
    any_ok = False
    for base, things_url in iter_sources(THINGS_PATH):
        try:
            for thing in fetch_paged(things_url):
                any_ok = True
                thing_id = thing.get("@iot.id")
                thing_name = thing.get("name")
                props = thing.get("properties")

                conn.execute(
                    "INSERT OR REPLACE INTO stations(thing_id, thing_name, thing_properties) VALUES(?,?,?)",
                    (thing_id, thing_name, json.dumps(props, ensure_ascii=False)),
                )

                # 展開 ObservedProperty 以提升分群準確率
                ds_url = f"{base.rstrip('/')}/Things({thing_id})/Datastreams?$expand=ObservedProperty"
                for ds in fetch_paged(ds_url):
                    ds_id = ds.get("@iot.id")
                    ds_name = ds.get("name")
                    metric = classify_metric_from_ds(ds)  # 可能得到 rainfall / water_level / discharge / ''
                    unit = (ds.get("unitOfMeasurement") or {}).get("name")

                    conn.execute(
                        "INSERT OR REPLACE INTO datastreams(ds_id, thing_id, ds_name, metric, unit) VALUES(?,?,?,?,?)",
                        (ds_id, thing_id, ds_name, metric, unit),
                    )

        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (404, 410):
                # 這個 BASE_URL 沒有對應資源，略過即可
                print("⚠️ source not found:", things_url)
                continue
            raise

    conn.commit()
    if not any_ok:
        raise RuntimeError(
            "No sources yielded data. 請確認 app_config.BASE_URLS（先用 STA_Rain/v1.0 驗證）。"
        )


def fetch_recent_observations(conn):
    """抓近 WINDOW_MIN 分鐘的 Observations，去重後寫進 raw_observations。"""
    since_utc = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=WINDOW_MIN)

    # 只抓「已判出 metric 的 datastream」
    cur = conn.execute("SELECT ds_id, thing_id FROM datastreams WHERE metric != ''")
    rows = cur.fetchall()

    for ds_id, thing_id in rows:
        found = False
        for base in BASE_URLS:
            obs_url = f"{base.rstrip('/')}/Datastreams({ds_id})/Observations"
            params = {
                "$filter": f"phenomenonTime ge {since_utc.isoformat()}",
                "$orderby": "phenomenonTime asc",
                "$top": 1000,
            }
            try:
                data = _get(obs_url, params)
                for obs in data.get("value", []):
                    t_utc = to_utc_dt(obs.get("phenomenonTime")).isoformat()
                    result = obs.get("result")
                    conn.execute(
                        "INSERT OR IGNORE INTO raw_observations(ds_id, thing_id, obs_time_utc, result, result_json) "
                        "VALUES(?,?,?,?,?)",
                        (
                            ds_id,
                            thing_id,
                            t_utc,
                            float(result) if result is not None else None,
                            json.dumps(obs, ensure_ascii=False),
                        ),
                    )
                found = True
                break
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code in (404, 410):
                    # 此庫沒有這個 ds_id 的 Observations，換下一個 BASE_URL 嘗試
                    continue
                else:
                    raise
        if not found:
            print(f"⚠️ no observation endpoint for ds_id={ds_id} in configured BASE_URLS")

    conn.commit()


if __name__ == "__main__":
    conn = ensure_conn()
    print("🔄 syncing catalog (stations & datastreams)...")
    sync_catalog(conn)
    print("🔄 fetching recent observations (last", WINDOW_MIN, "minutes)...")
    fetch_recent_observations(conn)
    conn.close()
    print("✅ Done fetching recent observations")
