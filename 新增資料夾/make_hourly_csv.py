import os
import pandas as pd
from datetime import datetime, timedelta, timezone
from dateutil import parser as dateparser
from common import ensure_conn, LOCAL_TZ
from app_config import OUTPUT_DIR, FILL_MISSING_GRID

def last_full_hour_local():
    now = datetime.now(LOCAL_TZ)
    return now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)

def hour_grid(hour_start_local):
    return [hour_start_local + timedelta(minutes=10 * i) for i in range(6)]

def get_station_metric_catalog(conn):
    q = (
        "SELECT DISTINCT d.thing_id AS station_id, s.thing_name AS station_name, d.metric "
        "FROM datastreams d LEFT JOIN stations s ON s.thing_id = d.thing_id "
        "WHERE COALESCE(d.metric,'') != ''"
    )
    return pd.read_sql_query(q, conn)

if __name__ == "__main__":
    conn = ensure_conn()

    hour_start_local = last_full_hour_local()
    hour_end_local = hour_start_local + timedelta(hours=1)
    hour_start_utc = hour_start_local.astimezone(timezone.utc)
    hour_end_utc = hour_end_local.astimezone(timezone.utc)

    df = pd.read_sql_query(
        """
        SELECT r.ds_id,
               r.thing_id AS station_id,
               r.obs_time_utc,
               r.result,
               s.thing_name AS station_name,
               d.metric AS metric
        FROM raw_observations r
        LEFT JOIN stations s    ON s.thing_id = r.thing_id
        LEFT JOIN datastreams d ON d.ds_id = r.ds_id
        WHERE r.obs_time_utc >= ? AND r.obs_time_utc < ?
          AND COALESCE(d.metric, '') != ''
        """,
        conn,
        params=(hour_start_utc.isoformat(), hour_end_utc.isoformat())
    )

    catalog = get_station_metric_catalog(conn)
    conn.close()

    os.makedirs(os.path.join(OUTPUT_DIR, hour_start_local.strftime("%Y/%m/%d")), exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, hour_start_local.strftime("%Y/%m/%d/%H.csv"))

    def to_local(dt_iso):
        return dateparser.isoparse(dt_iso).astimezone(LOCAL_TZ).replace(microsecond=0)

    if not df.empty:
        df["sample_time_dt"] = df["obs_time_utc"].apply(to_local)
        df["sample_time"] = df["sample_time_dt"].apply(lambda dt: dt.isoformat())
        df["hour"] = hour_start_local.isoformat()
        df.rename(columns={"result": "value"}, inplace=True)
        df = df[["hour", "sample_time", "station_id", "station_name", "metric", "value"]]
    else:
        df = pd.DataFrame(columns=["hour","sample_time","station_id","station_name","metric","value"]).astype({"station_id":"Int64"})

    # 只有在「有站與 metric」時才補時間格；避免出現只有時間、其他欄全空的假資料
    if FILL_MISSING_GRID:
        grid_times = [t.isoformat() for t in hour_grid(hour_start_local)]
        if not df.empty:
            stations = df[["station_id","station_name"]].drop_duplicates()
            metrics = df["metric"].drop_duplicates().to_frame(name="metric")
        else:
            stations = catalog[["station_id","station_name"]].drop_duplicates()
            metrics = catalog[["metric"]].drop_duplicates()

        if not stations.empty and not metrics.empty:
            base = (
                stations.assign(key=1)
                .merge(metrics.assign(key=1), on="key", how="outer")
                .drop("key", axis=1)
            )
            base = base.assign(hour=hour_start_local.isoformat())
            base = base.assign(key=1).merge(
                pd.DataFrame({"sample_time": grid_times, "key":[1]*len(grid_times)}),
                on="key", how="outer"
            ).drop("key", axis=1)

            df = base.merge(df, on=["hour","sample_time","station_id","station_name","metric"], how="left")

    df.sort_values(["station_id","metric","sample_time"], inplace=True)
    df.to_csv(out_path, index=False)
    print("✅ written:", out_path)
