import requests
import datetime
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import timedelta

class WeatherForecaster:
    region_xy = {
        "강원": [83, 130], "경기": [61, 124], "경남": [85, 77], "경북": [91, 100],
        "광주": [59, 74], "대구": [89, 91], "대전": [67, 100], "부산": [98, 75],
        "서울": [60, 126], "세종": [65, 104], "울산": [102, 84], "인천": [54, 125],
        "전남": [60, 68], "전북": [62, 87], "제주": [53, 36], "충남": [58, 104], "충북": [73, 109]
    }

    REGION_CODE_MAP = {
        "서울": ("11B00000", "11B10101"), "인천": ("11B00000", "11B20201"),
        "경기": ("11B00000", "11B20601"), "강원": ("11D10000", "11D10301"),
        "대전": ("11C20000", "11C20401"), "세종": ("11C20000", "11C20404"),
        "충북": ("11C10000", "11C10301"), "충남": ("11C20000", "11C20101"),
        "광주": ("11F20000", "11F20501"), "전북": ("11F10000", "11F10201"),
        "전남": ("11F20000", "11F20401"), "대구": ("11H10000", "11H10201"),
        "경북": ("11H10000", "11H10701"), "부산": ("11H20000", "11H20201"),
        "울산": ("11H20000", "11H20101"), "경남": ("11H20000", "11H20301"),
        "제주": ("11G00000", "11G00201")
    }

    sky_map = {'1': '맑음', '3': '구름많음', '4': '흐림'}
    pty_map = {'0': '없음', '1': '비', '2': '비/눈', '3': '눈', '4': '소나기'}

    def __init__(self, start_date: str, end_date: str, region_name: str, service_key: str):
        self.start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        self.region_name = region_name.strip()
        self.service_key = service_key
        self.today = datetime.datetime.now().date()

    def get_base_datetime(self):
        now = datetime.datetime.now()
        base_times = ['0200', '0500', '0800', '1100', '1400', '1700', '2000', '2300']
        now_time = now.strftime('%H%M')
        for bt in reversed(base_times):
            if now_time >= bt:
                return now.strftime('%Y%m%d'), bt
        return (now - timedelta(days=1)).strftime('%Y%m%d'), '2300'

    def get_short_term_forecast(self, date):
        nx, ny = self.region_xy.get(self.region_name, (60, 126))
        base_date, base_time = self.get_base_datetime()

        url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst'
        params = {
            'serviceKey': self.service_key,
            'pageNo': '1',
            'numOfRows': '1000',
            'dataType': 'XML',
            'base_date': base_date,
            'base_time': base_time,
            'nx': nx,
            'ny': ny
        }

        res = requests.get(url, params=params)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')

        data = []
        for item in items:
            fcstDate = item.findtext('fcstDate')
            if fcstDate != date.strftime('%Y%m%d'):
                continue
            category = item.findtext('category')
            fcstTime = item.findtext('fcstTime')
            fcstValue = item.findtext('fcstValue')
            data.append({'시간': fcstTime, '항목': category, '값': fcstValue})

        df = pd.DataFrame(data)
        if df.empty:
            return f"{date.strftime('%Y-%m-%d')} 📭 단기 예보 데이터 없음"

        sky = df[df['항목'] == 'SKY']['값'].mode()
        pty = df[df['항목'] == 'PTY']['값'].mode()
        pop = df[df['항목'] == 'POP']['값'].astype(int).max()
        tmp = df[df['항목'] == 'TMP']['값'].astype(float)
        min_temp = tmp.min()
        max_temp = tmp.max()

        return f"""
📅 {date.strftime('%Y-%m-%d')} 단기 예보
☁️ 하늘 상태: {self.sky_map.get(sky.iloc[0], '정보 없음') if not sky.empty else '정보 없음'}
🌧️ 강수 형태: {self.pty_map.get(pty.iloc[0], '정보 없음') if not pty.empty else '정보 없음'}
🌂 강수 확률: {pop}%
🌡️ 최저/최고 기온: {min_temp}℃ / {max_temp}℃
"""

    def get_mid_term_forecast(self, date):
        base_time = "0600" if datetime.datetime.now().hour < 18 else "1800"
        tmFc = datetime.datetime.now().strftime("%Y%m%d") + base_time
        reg = self.REGION_CODE_MAP.get(self.region_name)

        if not reg:
            return f"❌ '{self.region_name}' 지역은 지원되지 않습니다."

        regId_land, regId_temp = reg
        delta_days = (date.date() - self.today).days

        if not (3 <= delta_days <= 10):
            return f"❌ {date.strftime('%Y-%m-%d')} 중기예보는 3~10일 후 날짜만 지원됩니다."

        url_land = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst'
        params_land = {
            'serviceKey': self.service_key,
            'pageNo': '1',
            'numOfRows': '10',
            'dataType': 'XML',
            'regId': regId_land,
            'tmFc': tmFc
        }

        res_land = requests.get(url_land, params=params_land)
        root_land = ET.fromstring(res_land.content)
        item = root_land.find('.//item')

        if item is None:
            return f"⚠️ 중기 육상 예보 데이터가 없습니다 ({date.strftime('%Y-%m-%d')})"

        if 3 <= delta_days <= 7:
            wf_am = item.findtext(f'wf{delta_days}')
            rn_am = item.findtext(f'rnSt{delta_days}')
            weather = f"{wf_am}"
            rain = f"{rn_am}%"
        else:
            weather = item.findtext(f'wf{delta_days}')
            rain = item.findtext(f'rnSt{delta_days}') + "%"

        url_temp = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa'
        params_temp = {
            'serviceKey': self.service_key,
            'pageNo': '1',
            'numOfRows': '10',
            'dataType': 'XML',
            'regId': regId_temp,
            'tmFc': tmFc
        }

        res_temp = requests.get(url_temp, params=params_temp)
        root_temp = ET.fromstring(res_temp.content)
        item_temp = root_temp.find('.//item')

        if item_temp is None:
            min_temp, max_temp = "정보 없음", "정보 없음"
        else:
            min_temp = item_temp.findtext(f'taMin{delta_days}')
            max_temp = item_temp.findtext(f'taMax{delta_days}')

        return f"""
📅 {date.strftime('%Y-%m-%d')} 중기 예보
🌥️ 날씨 상태: {weather}
🌧️ 강수 확률: {rain}
🌡️ 최저/최고 기온: {min_temp}℃ / {max_temp}℃
"""

    def print_forecast(self):
        print("\n📊 날씨 정보 요약\n" + "="*30)
        for d in pd.date_range(self.start_date, self.end_date):
            delta = (d.date() - self.today).days
            if delta < 0:
                print(f"{d.strftime('%Y-%m-%d')} 🔹 이미 지난 날짜입니다.")
            elif 0 <= delta <= 4:
                print(self.get_short_term_forecast(d))
            elif 4 < delta <= 10:
                print(self.get_mid_term_forecast(d))
            else:
                print(f"{d.strftime('%Y-%m-%d')} 🔹 예보 불가 (10일 초과)")
if __name__ == "__main__":
    start = input("시작 날짜 (예: 2025-06-05): ")
    end = input("종료 날짜 (예: 2025-06-10): ")
    region = input("지역 (예: 서울): ")
    service_key = 'AdOnJCf1h6c12+MPkWOpvKxFe9q3XeC04ulEybksva9uaAdvXGc1onNOdLZ3TlBdJ4XMk0Sey+xWRKO3rQ+/4A=='

    wf = WeatherForecaster(start, end, region, service_key)
    wf.print_forecast()


import tkinter as tk
from tkinter import ttk, messagebox
import requests
import datetime
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import timedelta

# 기존 WeatherForecaster 클래스는 그대로 사용
# (생략 없이 그대로 위에 붙이세요)

class WeatherAppTableGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("🌤️ 여행 날씨 예보 테이블")
        self.master.geometry("900x500")

        # 입력 폼
        tk.Label(master, text="시작 날짜 (YYYY-MM-DD):").grid(row=0, column=0)
        self.start_entry = tk.Entry(master)
        self.start_entry.grid(row=0, column=1)

        tk.Label(master, text="종료 날짜 (YYYY-MM-DD):").grid(row=1, column=0)
        self.end_entry = tk.Entry(master)
        self.end_entry.grid(row=1, column=1)

        tk.Label(master, text="지역 (예: 서울):").grid(row=2, column=0)
        self.region_entry = tk.Entry(master)
        self.region_entry.grid(row=2, column=1)

        self.fetch_btn = tk.Button(master, text="날씨 예보 보기", command=self.fetch_forecast)
        self.fetch_btn.grid(row=3, column=0, columnspan=2, pady=10)

        # 테이블(표) 설정
        columns = ("날짜", "예보 구분", "하늘 상태", "강수 형태", "강수 확률", "최저 기온", "최고 기온")
        self.tree = ttk.Treeview(master, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.grid(row=4, column=0, columnspan=3, sticky="nsew")

        # 스크롤바
        scrollbar = ttk.Scrollbar(master, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=4, column=3, sticky='ns')

    def fetch_forecast(self):
        self.tree.delete(*self.tree.get_children())  # 기존 테이블 내용 초기화
        start = self.start_entry.get()
        end = self.end_entry.get()
        region = self.region_entry.get()
        service_key = 'AdOnJCf1h6c12+MPkWOpvKxFe9q3XeC04ulEybksva9uaAdvXGc1onNOdLZ3TlBdJ4XMk0Sey+xWRKO3rQ+/4A=='

        try:
            wf = WeatherForecaster(start, end, region, service_key)
            for d in pd.date_range(wf.start_date, wf.end_date):
                delta = (d.date() - wf.today).days
                if delta < 0:
                    continue
                elif 0 <= delta <= 4:
                    result = self.parse_short(wf.get_short_term_forecast(d))
                    if result:
                        self.tree.insert("", "end", values=result)
                elif 4 < delta <= 10:
                    result = self.parse_mid(wf.get_mid_term_forecast(d))
                    if result:
                        self.tree.insert("", "end", values=result)
        except Exception as e:
            messagebox.showerror("오류", f"예보 가져오기 실패:\n{str(e)}")

    def parse_short(self, text):
        try:
            lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
            날짜 = lines[0].replace("📅 ", "").replace(" 단기 예보", "")
            하늘 = lines[1].split(": ")[1]
            강수형태 = lines[2].split(": ")[1]
            강수확률 = lines[3].split(": ")[1]
            최저기온, 최고기온 = lines[4].split(": ")[1].replace("℃", "").split(" / ")
            return [날짜, "단기", 하늘, 강수형태, 강수확률, 최저기온, 최고기온]
        except:
            return None

    def parse_mid(self, text):
        try:
            lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
            날짜 = lines[0].replace("📅 ", "").replace(" 중기 예보", "")
            하늘 = lines[1].split(": ")[1]
            강수확률 = lines[2].split(": ")[1]
            최저기온, 최고기온 = lines[3].split(": ")[1].replace("℃", "").split(" / ")
            return [날짜, "중기", 하늘, 강수확률, 최저기온, 최고기온]
        except:
            return None

# 실행
if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherAppTableGUI(root)
    root.mainloop()
