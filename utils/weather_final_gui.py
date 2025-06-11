import requests
import datetime
import xml.etree.ElementTree as ET
import pandas as pd
import tkinter as tk
from tkinter import ttk
from datetime import timedelta

class WeatherForecaster:
    region_xy = {
        "강원": [83, 130], "경기": [61, 124], "경남": [91, 77], "경북": [91, 106],
        "광주": [59, 74], "대구": [89, 90], "대전": [67, 100], "부산": [98, 76],
        "서울": [60, 127], "세종": [66, 103], "울산": [102, 84], "인천": [55, 124],
        "전남": [51, 67], "전북": [63, 89], "제주": [52, 38], "충남": [68, 100], "충북": [69, 107]
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

    def __init__(self, start_date, end_date, region_name, service_key):
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
        nx, ny = self.region_xy.get(self.region_name, (60, 127))
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

        data = [item for item in items if item.findtext('fcstDate') == date.strftime('%Y%m%d')]
        if not data:
            return [date.strftime('%Y-%m-%d'), '데이터 없음', '', '', '']

        df = pd.DataFrame([{
            '항목': i.findtext('category'),
            '값': i.findtext('fcstValue')
        } for i in data])

        sky = df[df['항목'] == 'SKY']['값'].mode()
        pty = df[df['항목'] == 'PTY']['값'].mode()
        pop = df[df['항목'] == 'POP']['값'].astype(int).max()
        tmp = df[df['항목'] == 'TMP']['값'].astype(float)
        min_temp = tmp.min()
        max_temp = tmp.max()

        return [
            date.strftime('%Y-%m-%d'),
            self.sky_map.get(sky.iloc[0], '정보 없음') if not sky.empty else '정보 없음',
            self.pty_map.get(pty.iloc[0], '정보 없음') if not pty.empty else '정보 없음',
            f"{pop}%" if pop else "정보 없음",
            f"{min_temp}℃ / {max_temp}℃" if not tmp.empty else "정보 없음"
        ]

    def get_mid_term_forecast(self, date):
        tmFc = datetime.datetime.now().strftime("%Y%m%d") + ("0600" if datetime.datetime.now().hour < 18 else "1800")
        reg = self.REGION_CODE_MAP.get(self.region_name)
        delta = (date.date() - self.today).days

        if not reg or not (3 <= delta <= 10):
            return [date.strftime('%Y-%m-%d'), '지원 안됨', '', '', '']

        regId_land, regId_temp = reg

        res1 = requests.get('http://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst', params={
            'serviceKey': self.service_key,
            'pageNo': '1', 'numOfRows': '10',
            'dataType': 'XML', 'regId': regId_land, 'tmFc': tmFc
        })
        item1 = ET.fromstring(res1.content).find('.//item')

        res2 = requests.get('http://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa', params={
            'serviceKey': self.service_key,
            'pageNo': '1', 'numOfRows': '10',
            'dataType': 'XML', 'regId': regId_temp, 'tmFc': tmFc
        })
        item2 = ET.fromstring(res2.content).find('.//item')

        weather = item1.findtext(f'wf{delta}')
        rain = item1.findtext(f'rnSt{delta}')
        min_temp = item2.findtext(f'taMin{delta}')
        max_temp = item2.findtext(f'taMax{delta}')

        return [
            date.strftime('%Y-%m-%d'),
            weather or '정보 없음',
            '정보 없음',
            f"{rain}%" if rain else '정보 없음',
            f"{min_temp}℃ / {max_temp}℃" if min_temp and max_temp else '정보 없음'
        ]

    def collect_forecast_data(self):
        result = []
        for d in pd.date_range(self.start_date, self.end_date):
            delta = (d.date() - self.today).days
            if delta < 0 or delta > 10:
                result.append([d.strftime('%Y-%m-%d'), '예보 불가', '', '', ''])
            elif delta <= 3:
                result.append(self.get_short_term_forecast(d))
            else:
                result.append(self.get_mid_term_forecast(d))
        return result

class WeatherApp(tk.Tk):
    def __init__(self, forecast_data):
        super().__init__()
        self.title("날씨 예보 테이블")
        self.geometry("700x400")

        columns = ("날짜", "하늘 상태", "강수 형태", "강수 확률", "기온")
        tree = ttk.Treeview(self, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=130, anchor="center")

        for row in forecast_data:
            tree.insert("", tk.END, values=row)

        tree.pack(expand=True, fill="both")

if __name__ == "__main__":
    # 예시
    start = "2025-06-14"
    end = "2025-06-15"
    region = "서울"
    service_key = 'AdOnJCf1h6c12+MPkWOpvKxFe9q3XeC04ulEybksva9uaAdvXGc1onNOdLZ3TlBdJ4XMk0Sey+xWRKO3rQ+/4A=='

    wf = WeatherForecaster(start, end, region, service_key)
    forecast = wf.collect_forecast_data()

    app = WeatherApp(forecast)
    app.mainloop()
