import requests
import datetime
import xml.etree.ElementTree as ET

# 지역 이름 → 육상예보용(regId_land) & 기온예보용(regId_temp) 매핑
REGION_CODE_MAP = {
    "서울": ("11B00000", "11B10101"),
    "인천": ("11B00000", "11B20201"),
    "경기": ("11B00000", "11B20601"),
    "강원": ("11D10000", "11D10301"),
    "대전": ("11C20000", "11C20401"),
    "세종": ("11C20000", "11C20404"),
    "충북": ("11C10000", "11C10301"),
    "충남": ("11C20000", "11C20101"),
    "광주": ("11F20000", "11F20501"),
    "전북": ("11F10000", "11F10201"),
    "전남": ("11F20000", "11F20401"),
    "대구": ("11H10000", "11H10201"),
    "경북": ("11H10000", "11H10701"),
    "부산": ("11H20000", "11H20201"),
    "울산": ("11H20000", "11H20101"),
    "경남": ("11H20000", "11H20301"),
    "제주": ("11G00000", "11G00201")
}

def get_mid_weather(date_str, region_name):
    today = datetime.datetime.now()
    base_time = "0600" if today.hour < 18 else "1800"
    tmFc = today.strftime("%Y%m%d") + base_time

    # 지역 코드 매핑
    if region_name not in REGION_CODE_MAP:
        return "❌ 지원하지 않는 지역입니다. 예: 서울, 부산, 대전 등"

    regId_land, regId_temp = REGION_CODE_MAP[region_name]

    # 날짜 차이 계산
    target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    delta_days = (target_date - today.date()).days

    if delta_days < 3 or delta_days > 10:
        return "❌ 중기 예보는 오늘로부터 **3~10일 뒤**까지만 제공됩니다."

    # ===== API 요청 1 - 강수 및 날씨 =====
    url_land = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst'
    params_land = {
        'serviceKey': 'AdOnJCf1h6c12+MPkWOpvKxFe9q3XeC04ulEybksva9uaAdvXGc1onNOdLZ3TlBdJ4XMk0Sey+xWRKO3rQ+/4A==',
        'pageNo': '1',
        'numOfRows': '10',
        'dataType': 'XML',
        'regId': regId_land,
        'tmFc': tmFc
    }

    res_land = requests.get(url_land, params=params_land)
    root_land = ET.fromstring(res_land.content)
    item_land = root_land.find('.//item')

    if 3 <= delta_days <= 7:
        wf_am = item_land.findtext(f'wf{delta_days}Am') or "정보 없음"
        wf_pm = item_land.findtext(f'wf{delta_days}Pm') or "정보 없음"
        rn_am = item_land.findtext(f'rnSt{delta_days}Am') or "정보 없음"
        rn_pm = item_land.findtext(f'rnSt{delta_days}Pm') or "정보 없음"
        weather = f"오전: {wf_am}, 오후: {wf_pm}"
        rain = f"오전: {rn_am}%, 오후: {rn_pm}%"
    else:
        weather = item_land.findtext(f'wf{delta_days}') or "정보 없음"
        rain = (item_land.findtext(f'rnSt{delta_days}') or "정보 없음") + "%"

    # ===== API 요청 2 - 기온 =====
    url_temp = 'http://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa'
    params_temp = {
        'serviceKey': 'AdOnJCf1h6c12+MPkWOpvKxFe9q3XeC04ulEybksva9uaAdvXGc1onNOdLZ3TlBdJ4XMk0Sey+xWRKO3rQ+/4A==',
        'pageNo': '1',
        'numOfRows': '10',
        'dataType': 'XML',
        'regId': regId_temp,
        'tmFc': tmFc
    }

    res_temp = requests.get(url_temp, params=params_temp)
    root_temp = ET.fromstring(res_temp.content)
    item_temp = root_temp.find('.//item')

    min_temp = item_temp.findtext(f'taMin{delta_days}') or "정보 없음"
    max_temp = item_temp.findtext(f'taMax{delta_days}') or "정보 없음"

    # 출력
    result = f"""📍 {region_name} 지역 {date_str} 중기 예보:
🔸 날씨 상태: {weather}
🔸 강수 확률: {rain}
🌡️ 최저기온: {min_temp}℃ / 최고기온: {max_temp}℃
"""
    return result


# ===== 사용자 입력 =====
date_input = input("날짜를 입력하세요 (예: 2025-06-10): ")
region_input = input("지역을 입력하세요 (예: 서울, 부산, 대전): ")
print(get_mid_weather(date_input, region_input.strip()))
