from datetime import datetime
import calendar

# Julian Date 計算公式
def julian_date(year, month, day, hour, minute, second):
    """
    計算 Julian Date (JD)，將公元年份、月份、日期和時間轉換為 Julian Date。
    """
    if month <= 2:
        month += 12
        year -= 1
    
    A = year // 100
    B = 2 - A + A // 4
    
    # Julian Date 計算公式
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5
    jd += (hour + minute / 60 + second / 3600) / 24  # 加上小時、分鐘、秒的部分
    return jd

def time_to_julian_date():
    # 請用戶輸入時間
    user_input = input("請輸入時間 (格式：YYYY-MM-DD HH:MM): ")
    try:
        # 轉換用戶輸入的時間為 datetime 物件
        input_time = datetime.strptime(user_input, "%Y-%m-%d %H:%M")
        
        # 計算該天是星期幾
        weekday = calendar.day_name[input_time.weekday()]
        
        # 計算該時間的 Julian Date
        jd_input = julian_date(input_time.year, input_time.month, input_time.day,
                               input_time.hour, input_time.minute, input_time.second)
        
        # 當前時間的 Julian Date
        now = datetime.utcnow()
        jd_now = julian_date(now.year, now.month, now.day, now.hour, now.minute, now.second)
        
        # 計算經過的太陽日數
        days_passed = jd_now - jd_input
        
        # 顯示結果
        print(f"您輸入的日期時間是: {input_time}")
        print(f"該日期是星期 {weekday}")
        print(f"從該時刻至今經過了 {days_passed:.6f} 太陽日(Julian Date)。")
    except ValueError:
        print("輸入的時間格式不正確，請確保格式為 YYYY-MM-DD HH:MM。")

# 執行函數
time_to_julian_date()
