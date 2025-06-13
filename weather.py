import requests
import datetime
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import timedelta

# ── 단기 예보용 지역 좌표 ─────────────────────────────
region_xy = {
    "강원": [83, 130], "경기": [61, 124], "경남": [85, 77], "경북": [91, 100],
    "광주": [59, 74], "대구": [89, 91], "대전": [67, 100], "부산": [98, 75],
    "서울": [60, 126], "세종": [65, 104], "울산": [102, 84], "인천": [54, 125],
    "전남": [60, 68], "전북": [62, 87], "제주": [53, 36], "충남": [58, 104], "충북": [73, 109]
}

# ── 중기 예보용 지역 코드 ─────────────────────────────
REGION_CODE_MAP = {
    "서울": ("11B00000", "11B10101"), "인천": ("11B00000", "11B20201"), "경기": ("11B00000", "11B20601"),
    "강원": ("11D10000", "11D10301"), "대전": ("11C20000", "11C20401"), "세종": ("11C20000", "11C20404"),
    "충북": ("11C10000", "11C10301"), "충남": ("11C20000", "11C20101"), "광주": ("11F20000", "11F20501"),
    "전북": ("11F10000", "11F10201"), "전남": ("11F20000", "11F20401"), "대구": ("11H10000", "11H10201"),
    "경북": ("11H10000", "11H10701"), "부산": ("11H20000", "11H20201"), "울산": ("11H20000", "11H20101"),
    "경남": ("11H20000", "11H20301"), "제주": ("11G00000", "11G00201")
}

sky_map = {'1': '맑음', '3': '구름많음', '4': '흐림'}
pty_map = {'0': '없음', '1': '비', '2': '비/눈', '3': '눈', '4': '소나기'}

service_key = 'AdOnJCf1h6c12+MPkWOpvKxFe9q3XeC04ulEybksva9uaAdvXGc1onNOdLZ3TlBdJ4XMk0Sey+xWRKO3rQ+/4A=='

# ── 캐시 ─────────────────────────────
weather_cache = {"short": {}, "mid": {}}

# ── 단기 예보 base 시간 계산 ─────────────────────────────
def get_base_datetime():
    now = datetime.datetime.now()
    base_times = ['0200', '0500', '0800', '1100', '1400', '1700', '2000', '2300']
    now_time = now.strftime('%H%M')
    for bt in reversed(base_times):
        if now_time >= bt:
            return now.strftime('%Y%m%d'), bt
    return (now - timedelta(days=1)).strftime('%Y%m%d'), '2300'

# ── 단기 예보 ─────────────────────────────
def get_short_term_forecast(date_obj, region_name):
    key = (date_obj.strftime('%Y-%m-%d'), region_name)
    if key in weather_cache["short"]:
        return weather_cache["short"][key]

    nx, ny = region_xy.get(region_name, (60, 126))
    base_date, base_time = get_base_datetime()

    url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst'
    params = {
        'serviceKey': service_key,
        'pageNo': '1', 'numOfRows': '1000', 'dataType': 'XML',
        'base_date': base_date, 'base_time': base_time,
        'nx': nx, 'ny': ny
    }

    res = requests.get(url, params=params)
    root = ET.fromstring(res.content)
    items = root.findall('.//item')

    data = []
    for item in items:
        if item.findtext('fcstDate') != date_obj.strftime('%Y%m%d'):
            continue
        data.append({
            '시간': item.findtext('fcstTime'),
            '항목': item.findtext('category'),
            '값': item.findtext('fcstValue')
        })
    df = pd.DataFrame(data)

    if df.empty:
        return f"{date_obj.strftime('%Y-%m-%d')} 📭 단기 예보 데이터 없음"

    sky = df[df['항목'] == 'SKY']['값'].mode()
    pty = df[df['항목'] == 'PTY']['값'].mode()
    pop = df[df['항목'] == 'POP']['값'].astype(int).max()
    tmp = df[df['항목'] == 'TMP']['값'].astype(float)
    min_temp, max_temp = tmp.min(), tmp.max()

    result = (
        f"📅 {date_obj.strftime('%Y-%m-%d')} 단기 예보\n"
        f"☁️ 하늘 상태: {sky_map.get(sky.iloc[0], '정보 없음') if not sky.empty else '정보 없음'}\n"
        f"🌧️ 강수 형태: {pty_map.get(pty.iloc[0], '정보 없음') if not pty.empty else '정보 없음'}\n"
        f"🌂 강수 확률: {pop}%\n"
        f"🌡️ 최저/최고 기온: {min_temp}℃ / {max_temp}℃"
    )
    weather_cache["short"][key] = result
    return result

# ── 중기 예보 ─────────────────────────────
def get_mid_term_forecast(date_obj, region_name):
    key = (date_obj.strftime('%Y-%m-%d'), region_name)
    if key in weather_cache["mid"]:
        return weather_cache["mid"][key]

    today = datetime.datetime.now()
    base_time = "0600" if today.hour < 18 else "1800"
    tmFc = today.strftime("%Y%m%d") + base_time
    reg = REGION_CODE_MAP.get(region_name)

    if not reg:
        return f"❌ '{region_name}' 지역은 지원되지 않습니다."

    delta_days = (date_obj.date() - today.date()).days
    if not (3 <= delta_days <= 10):
        return f"❌ {date_obj.strftime('%Y-%m-%d')} 중기예보는 3~10일 후 날짜만 지원됩니다."

    regId_land, regId_temp = reg

    url_land = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst'
    params_land = {
        'serviceKey': service_key, 'pageNo': '1', 'numOfRows': '10',
        'dataType': 'XML', 'regId': regId_land, 'tmFc': tmFc
    }
    res_land = requests.get(url_land, params=params_land)
    item = ET.fromstring(res_land.content).find('.//item')

    if item is None:
        return f"⚠️ 중기 육상 예보 데이터가 없습니다 ({date_obj.strftime('%Y-%m-%d')})"

    if delta_days <= 7:
        weather = f"오전: {item.findtext(f'wf{delta_days}Am')}, 오후: {item.findtext(f'wf{delta_days}Pm')}"
        rain = f"오전: {item.findtext(f'rnSt{delta_days}Am')}%, 오후: {item.findtext(f'rnSt{delta_days}Pm')}%"
    else:
        weather = item.findtext(f'wf{delta_days}')
        rain = item.findtext(f'rnSt{delta_days}') + "%"

    url_temp = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa'
    params_temp = {
        'serviceKey': service_key, 'pageNo': '1', 'numOfRows': '10',
        'dataType': 'XML', 'regId': regId_temp, 'tmFc': tmFc
    }
    res_temp = requests.get(url_temp, params=params_temp)
    item_temp = ET.fromstring(res_temp.content).find('.//item')

    if item_temp is None:
        min_temp, max_temp = "정보 없음", "정보 없음"
    else:
        min_temp = item_temp.findtext(f'taMin{delta_days}')
        max_temp = item_temp.findtext(f'taMax{delta_days}')

    result = (
        f"📅 {date_obj.strftime('%Y-%m-%d')} 중기 예보\n"
        f"🌥️ 날씨 상태: {weather}\n"
        f"🌧️ 강수 확률: {rain}\n"
        f"🌡️ 최저/최고 기온: {min_temp}℃ / {max_temp}℃"
    )
    weather_cache["mid"][key] = result
    return result
