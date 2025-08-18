# peek_sta.py — 不加過濾，直接抓前 20 筆 Datastreams，看看實際 name/ObservedProperty/unit/Thing
import requests, pprint

BASES = [
    "https://sta.ci.taiwan.gov.tw/STA_Rain/v1.0",
    # 若你想一起看其它庫，也可以放進來（就算 404 也沒關係）
    "https://sta.ci.taiwan.gov.tw/STA_River/v1.0",
    "https://sta.ci.taiwan.gov.tw/STA_Hydro/v1.0",
]

def peek(base):
    url = f"{base.rstrip('/')}/Datastreams"
    params = {
        "$top": 20,
        "$expand": "ObservedProperty,Thing",
        # 不要加 $filter，先看原貌
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ {base} error:", e)
        return
    data = r.json().get("value", [])
    if not data:
        print(f"⚠️ {base} has no Datastreams (or requires different path)")
        return
    print(f"✅ {base} samples:")
    for i, ds in enumerate(data, 1):
        print(f"[{i}] ds_id={ds.get('@iot.id')} name={ds.get('name')!r}")
        op = (ds.get('ObservedProperty') or {})
        thing = (ds.get('Thing') or {})
        unit = (ds.get('unitOfMeasurement') or {})
        print("    ObservedProperty.name:", op.get("name"))
        print("    Thing.name:", thing.get("name"))
        print("    unit.name/symbol:", unit.get("name"), "/", unit.get("symbol"))
    print("-"*60)

def main():
    for b in BASES:
        peek(b)

if __name__ == "__main__":
    main()
