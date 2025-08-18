# init_db.py
from common import ensure_conn, ensure_columns

SCHEMA = """
CREATE TABLE IF NOT EXISTS stations (
  thing_id INTEGER PRIMARY KEY,
  thing_name TEXT,
  thing_properties TEXT
);

CREATE TABLE IF NOT EXISTS datastreams (
  ds_id INTEGER PRIMARY KEY,
  thing_id INTEGER,
  ds_name TEXT,
  ds_description TEXT,
  obsprop_name TEXT,
  metric TEXT,
  unit TEXT,
  FOREIGN KEY(thing_id) REFERENCES stations(thing_id)
);

CREATE TABLE IF NOT EXISTS raw_observations (
  ds_id INTEGER,
  thing_id INTEGER,
  obs_time_utc TEXT,
  result REAL,
  result_json TEXT,
  PRIMARY KEY (ds_id, obs_time_utc),
  FOREIGN KEY(ds_id) REFERENCES datastreams(ds_id),
  FOREIGN KEY(thing_id) REFERENCES stations(thing_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_time ON raw_observations(obs_time_utc);
"""

def main():
    conn = ensure_conn()
    conn.executescript(SCHEMA)
    # 平滑升級舊 DB（補欄位）
    ensure_columns(conn, "datastreams", {
        "ds_description": "TEXT",
        "obsprop_name": "TEXT",
        "unit": "TEXT",
    })
    conn.commit()
    conn.close()
    print("✅ DB initialized / migrated")

if __name__ == "__main__":
    main()
