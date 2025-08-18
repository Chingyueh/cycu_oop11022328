# fetch_10min.py
import json, requests
from datetime import datetime, timedelta, timezone

from common import ensure_conn, fetch_paged, _get, to_utc_dt, classify_metric_from_ds
from app_config import (
    BASE_URLS, WINDOW_MIN,
    API_FILTER_ENABLED, API_FILTER_AUTHORITIES, CATEGORY_WHITELIST_SUBSTR
)

def iter_sources(path_suffix: str):
    for base in BASE_URLS:
        yield base, f"{base.rstrip('/')}/{path_suffix.lstrip('/')}"

THINGS_PATH = "Things"

def _build_api_filter() -> str | None:
    """把程式端白名單轉成 API 的 $filter 字串（可選）。"""
    if not API_FILTER_ENABLED:
        return None

    parts = []

    # 類別白名單 → substringof('xxx', description)
    if CATEGORY_WHITELIST_SUBSTR:
        cats = [f"substringof('{s}', description)" for s in CATEGORY_WHITELIST_SUBSTR]
        parts.append("(" + " or ".join(cats) + ")")

    # 權責單位 → Thing/properties/authority_type eq '...'
    if API_FILTER_AUTHORITIES:
        auths = [f"Thing/properties/authority_type eq '{a}'" for a in API_FILTER_AUTHORITIES]
        parts.append("(" + " or ".join(auths) + ")")

    if not parts:
        return None
    return " and ".join(parts)

def sync_catalog(conn):
    """同步 stations / datastreams；展開 ObservedProperty, Thing；可選 API 過濾。"""
    any_ok = False
    for base, things_url in iter_sources(THINGS_PATH):
        try:
            # stations
            for thing in fetch_paged(things_url):
                any_ok = True
                thing_id = thing.get("@iot.id")
                thing_name = thing.get("name")
                props = thing.get("properties")
                conn.execute(
                    "INSERT OR REPLACE INTO stations(thing_id, thing_name, thing_properties) VALUES(?,?,?)",
                    (thing_id, thing_name, json.dumps(props, ensure_ascii=False)),
                )

                # datastreams with expand & optional $filter
                ds_url = f"{base.rstrip('/')}/Things({thing_id})/Datastreams"
                params = {"$expand": "ObservedProperty,Thing"}
                fil = _build_api_filter()
                if fil:
                    params["$filter"] = fil

                for ds in fetch_paged(ds_url, params=params):
                    ds_id = ds.get("@iot.id")
                    ds_name = ds.get("name")
                    ds_desc = ds.get("description")
                    obsprop = (ds.get("ObservedProperty") or {}).get("name")
                    unit = (ds.get("unitOfMeasurement") or {}).get("name")

                    metric = classify_metric_from_ds(ds)

                    conn.execute(
                        """
                        INSERT OR REPLACE INTO datastreams
                        (ds_id, thing_id, ds_name, ds_description, obsprop_name, metric, unit)
                        VALUES(?,?,?,?,?,?,?)
                        """,
                        (ds_id, thing_id, ds_name, ds_desc, obsprop, metric, unit),
                    )

        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (404, 410):
                print("⚠️ source not found:", things_url)
                continue
            raise

    conn.commit()
    if not any_ok:
        raise RuntimeError("No sources yielded data. Check BASE_URLS in app_config.py")

def fetch_recent_observations(conn):
    """抓近 WINDOW_MIN 分鐘 Observations，去重寫入 DB。"""
    since_utc = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=WINDOW_MIN)
    cur = conn.execute("SELECT ds_id, thing_id FROM datastreams WHERE COALESCE(metric,'') != ''")
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
                        "INSERT OR IGNORE INTO raw_observations(ds_id, thing_id, obs_time_utc, result, result_json) VALUES(?,?,?,?,?)",
                        (ds_id, thing_id, t_utc, float(result) if result is not None else None, json.dumps(obs, ensure_ascii=False)),
                    )
                found = True
                break
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code in (404, 410):
                    continue
                else:
                    raise
        if not found:
            print(f"⚠️ no observation endpoint for ds_id={ds_id} in configured BASE_URLS")
    conn.commit()

def main():
    conn = ensure_conn()
    print("🔄 syncing catalog (stations & datastreams)... API filter:", "ON" if API_FILTER_ENABLED else "OFF")
    sync_catalog(conn)
    print(f"🔄 fetching recent observations (last {WINDOW_MIN} minutes)...")
    fetch_recent_observations(conn)
    conn.close()
    print("✅ Done fetching recent observations")

if __name__ == "__main__":
    main()
