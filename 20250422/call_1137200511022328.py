from geojson_to_html import geojson_to_html

if __name__ == '__main__':
    # 指定輸入的 GeoJSON 檔案和輸出的 HTML 檔案
    inputfile = "20250422/bus_stop2.geojson"
    outputfile = "bus_stops.html"

    # 呼叫 geojson_to_html 函式來進行轉換
    geojson_to_html(inputfile, outputfile)