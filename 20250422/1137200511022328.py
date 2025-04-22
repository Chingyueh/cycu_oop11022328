import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt

def draw_geojson_to_png(inputfile: str, outputfile: str):
    # 讀取 bus_stop2.geojson
    bus_stops = gpd.read_file("20250422/bus_stop2.geojson")

    # 繪製所有公車站點
    fig, ax = plt.subplots(figsize=(10, 10))
    bus_stops.plot(ax=ax, color='blue', markersize=5)
    plt.title("Bus Stops")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

    # 儲存為 PNG 檔案
    plt.savefig("20250422/bus_stops.png")
    plt.close()