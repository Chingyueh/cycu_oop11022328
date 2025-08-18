# make_hourly_csv.py —— 整合版（可直接覆蓋）
# 依 metric 分檔輸出小時 CSV：
# output/<metric>/hourly/YYYY/MM/DD/<metric>_<HH>.csv
import os, json, argparse
import pandas as pd
from datetime import datetime, timedelta, timezone
from dateutil import parser as dateparser

from common import ensure_conn, LOCAL_TZ
from app_config import OUTPUT_ROOT, FILL_MISSING_GRID, ALLOW_AUTHORITIES, CATEGORY_WHITELIST_SUBSTR


def last_full_hour_local() -> datetime:
    now = datetime.now(LOCAL_TZ)
    return now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)


def current_hour_start_local() -> datetime:
    now = datetime.now(LOCAL_TZ)
    return now.replace(minute=0, second=0, microsecond=0)


def hour_grid(hour_start_local: datetime):
    # 6 個 10 分鐘格（:00, :10, :20, :30, :40, :50）
    return [hour_start_local + timedelta(minutes=10 * i) for i in range(6)]


def _authority_allowed(props_text: str) -> bool:
    """依 thing_properties.authority_type 白名單過濾（留空表示不過濾）。"""
    if not ALLOW_AUTHORITIES:
        return True
    try:
        props = json.loads(props_text or "{}")
        a = (props.get("authority_type") or "").strip()
        return any(a == allow for allow in ALLOW_AUTHORITIES)
    except Exception:
        return False


def _category_allowed(description_text: str) -> bool:
    """依 Datastream.description 內含字串白名單過濾（留空表示不過濾）。"""
    if not CATEGORY_WHITELIST_SUBSTR:
        return True
    txt = (description_text or "")
    return any(substr in txt for substr in CATEGORY_WHITELIST_SUBSTR)


def _to_local_iso(dt_iso: str) -> str:
    return dateparser.isoparse(dt_iso).astimezone(LOCAL_TZ).replace(microsecond=0).isoformat()


def _load_hour_dataframe(conn, hour_start_utc: datetime, hour_end_utc: datetime) -> pd.DataFrame:
    df = pd.read_sql_query(
        """
        SELECT r.ds_id,
               r.thing_id AS station_id,
               r.obs_time_utc,
               r.result,
               s.thing_name      AS station_name,
               s.thing_properties AS station_props,
               d.metric          AS metric,
               d.ds_description  AS ds_description
        FROM raw_observations r
        LEFT JOIN stations s    ON s.thing_id = r.thing_id
        LEFT JOIN datastreams d ON d.ds_id   = r.ds_id
        WHERE r.obs_time_utc >= ? AND r.obs_time_utc < ?
          AND COALESCE(d.metric, '') != ''
        """,
        conn,
        params=(hour_start_utc.isoformat(), hour_end_utc.isoformat()),
    )

    # 程式端白名單（類別）與權責單位過濾
    if not df.empty and CATEGORY_WHITELIST_SUBSTR:
        df = df[df["ds_description"].apply(_category_allowed)]
    if not df.empty and ALLOW_AUTHORITIES:
        df = df[df["station_props"].apply(_authority_allowed)]

    return df


def _emit_one_metric_csv(df_all: pd.DataFrame, metric: str, hour_start_local: datetime, is_current: bool):
    df = df_all[df_all["metric"] == metric].copy()

    out_dir = os.path.join(OUTPUT_ROOT, metric, "hourly", hour_start_local.strftime("%Y/%m/%d"))
    os.makedirs(out_dir, exist_ok=True)
    # ⬇️ 改成 metric_HH.csv
    out_path = os.path.join(out_dir, f"{metric}_{hour_start_local.strftime('%H')}.csv")

    # 當前小時或上一小時：允許部分資料
    if df.empty and not FILL_MISSING_GRID:
        pd.DataFrame(columns=["hour", "sample_time", "station_id", "station_name", "metric", "value"]).to_csv(out_path, index=False)
        tag = "current hour" if is_current else "last full hour"
        print(f"⚠️ [{metric}] no data for {tag}:", hour_start_local.isoformat())
        return out_path

    if not df.empty:
        df["sample_time"] = df["obs_time_utc"].apply(_to_local_iso)
        df["hour"] = hour_start_local.isoformat()
        df.rename(columns={"result": "value"}, inplace=True)
        df = df[["hour", "sample_time", "station_id", "station_name", "metric", "value"]]
    else:
        df = pd.DataFrame(columns=["hour", "sample_time", "station_id", "station_name", "metric", "value"]).astype({"station_id": "Int64"})

    # 是否補滿六個 10 分鐘格（缺值留空）
    if FILL_MISSING_GRID:
        grid_times = [t.isoformat() for t in hour_grid(hour_start_local)]
        if not df.empty:
            stations = df[["station_id", "station_name"]].drop_duplicates()
        else:
            stations = pd.DataFrame(columns=["station_id", "station_name"])

        if not stations.empty:
            base = stations.assign(key=1)
            base = base.assign(hour=hour_start_local.isoformat())
            base = base.assign(key=1).merge(
                pd.DataFrame({"sample_time": grid_times, "key": [1] * len(grid_times)}),
                on="key", how="outer"
            ).drop("key", axis=1)
            base["metric"] = metric
            df = base.merge(df, on=["hour", "sample_time", "station_id", "station_name", "metric"], how="left")

    df.sort_values(["station_id", "sample_time"], inplace=True)
    df.to_csv(out_path, index=False)
    tag = "current" if is_current else "last"
    print(f"✅ written [{metric}] ({tag} hour):", out_path)
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Export hourly CSV per metric (last full hour by default).")
    parser.add_argument("--current", action="store_true", help="Export for the current (incomplete) hour instead of last full hour.")
    args = parser.parse_args()

    # 決定小時區間
    hour_start_local = current_hour_start_local() if args.current else last_full_hour_local()
    hour_end_local = hour_start_local + timedelta(hours=1)
    hour_start_utc = hour_start_local.astimezone(timezone.utc)
    hour_end_utc = hour_end_local.astimezone(timezone.utc)

    conn = ensure_conn()
    df_all = _load_hour_dataframe(conn, hour_start_utc, hour_end_utc)
    conn.close()

    if df_all.empty and not FILL_MISSING_GRID:
        tag = "current hour" if args.current else "last full hour"
        print(f"⚠️ no data for {tag}:", hour_start_local.isoformat())
        return

    metrics = sorted(df_all["metric"].dropna().unique().tolist()) if not df_all.empty else []
    if not metrics:
        # 仍嘗試各 metric 建空框架（若 FILL_MISSING_GRID=False 則實際會寫空檔）
        metrics = [
            "rainfall",
            "river_water_level",
            "groundwater_level",
            "drainage_water_level",
            "discharge",
            "discharge_cum",
        ]

    for m in metrics:
        _emit_one_metric_csv(df_all, m, hour_start_local, args.current)


if __name__ == "__main__":
    main()
