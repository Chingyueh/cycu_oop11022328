# list_datastreams.py
import requests
from app_config import BASE_URLS

def list_datastreams(base_url, top=50):
    url = f"{base_url}/Datastreams?$top={top}&$expand=ObservedProperty,Thing"
    print(f"\n🔎 Checking {base_url}")
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"❌ error: {e}")
        return

    data = r.json()
    ds_list = data.get("value", [])
    for ds in ds_list:
        name = ds.get("name") or ""
        obs = ds.get("ObservedProperty", {}).get("name") or ""
        thing = ds.get("Thing", {}).get("name") or ""
        print(f"📌 {name} | ObsProp: {obs} | Station: {thing}")

if __name__ == "__main__":
    for base in BASE_URLS:
        list_datastreams(base, top=100)  # 每個端點列前 100 筆
